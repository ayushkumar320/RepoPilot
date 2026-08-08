"use client";

import dagre from "@dagrejs/dagre";
import { GraphIcon } from "@phosphor-icons/react";
import {
  Background,
  Controls,
  type Edge,
  MarkerType,
  type Node,
  ReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useCallback, useMemo, useState } from "react";

import {
  ApiError,
  api,
  type GraphModule,
  type GraphModulesResponse,
} from "../lib/api/generated";

/**
 * Box size, in the layout's units.
 *
 * Dagre needs a size before anything is rendered, so these are fixed rather
 * than measured. The CSS uses the same numbers — a mismatch shows up as
 * overlapping boxes or as gaps that look like a broken layout.
 */
const NODE_WIDTH = 190;
const NODE_HEIGHT = 52;

type LoadState =
  | { phase: "idle" }
  | { phase: "loading" }
  | { phase: "error"; message: string }
  | { phase: "loaded"; data: GraphModulesResponse };

/**
 * Lay the map out top-down with dagre.
 *
 * Deliberately not a force simulation: this graph is a dependency hierarchy,
 * and a layered layout puts what-depends-on-what on the vertical axis where it
 * can be read. A force layout would also animate its way to a resting position,
 * which is motion this app promises not to produce for readers who asked for
 * none.
 */
function layout(data: GraphModulesResponse): { nodes: Node[]; edges: Edge[] } {
  const graph = new dagre.graphlib.Graph();
  graph.setDefaultEdgeLabel(() => ({}));
  graph.setGraph({ rankdir: "TB", nodesep: 28, ranksep: 64 });

  for (const module of data.modules) {
    graph.setNode(module.symbol, { width: NODE_WIDTH, height: NODE_HEIGHT });
  }
  for (const edge of data.edges) {
    graph.setEdge(edge.source, edge.target);
  }
  dagre.layout(graph);

  const nodes: Node[] = data.modules.map((module) => {
    const placed = graph.node(module.symbol);
    return {
      id: module.symbol,
      // dagre returns a centre point; React Flow positions by top-left corner.
      position: { x: placed.x - NODE_WIDTH / 2, y: placed.y - NODE_HEIGHT / 2 },
      data: { label: <ModuleBox module={module} /> },
      style: { width: NODE_WIDTH, height: NODE_HEIGHT },
      className: "module-node",
    };
  });

  const edges: Edge[] = data.edges.map((edge) => ({
    id: `${edge.source}->${edge.target}`,
    source: edge.source,
    target: edge.target,
    // Never `animated: true`. A marching-ants edge is decoration that the
    // reduced-motion contract would have to undo.
    markerEnd: { type: MarkerType.ArrowClosed, width: 14, height: 14 },
  }));

  return { nodes, edges };
}

function ModuleBox({ module }: { module: GraphModule }) {
  return (
    <span className="module-box">
      <span className="module-box-name">{module.label}</span>
      <span className="module-box-meta">
        {module.depended_on_by} in · {module.depends_on} out
      </span>
    </span>
  );
}

export function ModuleMap({ repoId }: { repoId: string }) {
  const [expanded, setExpanded] = useState(false);
  const [state, setState] = useState<LoadState>({ phase: "idle" });
  const [selected, setSelected] = useState<GraphModule | null>(null);

  const open = useCallback(async () => {
    if (expanded) {
      setExpanded(false);
      return;
    }
    setExpanded(true);
    if (state.phase !== "idle") return;
    setState({ phase: "loading" });
    try {
      setState({ phase: "loaded", data: await api.getGraphModules(repoId) });
    } catch (caught) {
      setState({
        phase: "error",
        message:
          caught instanceof ApiError ? caught.message : "Could not load the module map right now.",
      });
    }
  }, [expanded, state.phase, repoId]);

  // Narrowed once, so the JSX below can read it without re-proving the phase
  // inside every branch.
  const data = state.phase === "loaded" ? state.data : null;

  // Laying out ~100 boxes is not free, and React Flow re-renders on every pan.
  const flow = useMemo(() => (data && data.available ? layout(data) : null), [data]);

  const onNodeClick = useCallback(
    (_: unknown, node: Node) => {
      setSelected(data?.modules.find((m) => m.symbol === node.id) ?? null);
    },
    [data],
  );

  return (
    <section className="module-map">
      <button
        type="button"
        className="neighbours-toggle"
        aria-expanded={expanded}
        onClick={() => void open()}
      >
        <GraphIcon size={15} aria-hidden="true" />
        Module map
      </button>

      {expanded ? (
        <div className="module-map-body">
          {state.phase === "loading" ? (
            <p className="neighbour-note">Reading the code graph…</p>
          ) : null}
          {state.phase === "error" ? <p className="neighbour-note">{state.message}</p> : null}
          {data && !data.available ? (
            <p className="neighbour-note">
              No module map for this repository. Dependency graphs are built from Python source.
            </p>
          ) : null}
          {data?.available && data.modules.length === 0 ? (
            <p className="neighbour-note">This snapshot has no modules that import one another.</p>
          ) : null}

          {flow && flow.nodes.length > 0 ? (
            <>
              <div className="module-map-canvas">
                <ReactFlow
                  nodes={flow.nodes}
                  edges={flow.edges}
                  onNodeClick={onNodeClick}
                  fitView
                  // Cap the zoom at 1. Without it, fitView scales a small map
                  // up until three boxes fill the canvas, which reads as a
                  // rendering fault rather than as a small repository.
                  fitViewOptions={{ maxZoom: 1, padding: 0.15 }}
                  // The layout is authoritative; dragging a box would only let
                  // a reader destroy the arrangement that carries the meaning.
                  nodesDraggable={false}
                  nodesConnectable={false}
                  proOptions={{ hideAttribution: false }}
                >
                  <Background />
                  <Controls showInteractive={false} />
                </ReactFlow>
              </div>

              <p className="neighbour-note">
                {data?.truncated
                  ? `Showing the ${data.modules.length} busiest of ${data.total_modules} modules, ${flow.edges.length} of ${data.total_edges} dependencies.`
                  : `${data?.modules.length ?? 0} modules, ${data?.total_edges ?? 0} dependencies.`}
              </p>

              {selected ? (
                <div className="module-map-detail">
                  <strong>{selected.symbol}</strong>
                  <span className="neighbour-ref">
                    {/* A module with no chunk is still a real dependency
                        target; say so rather than inventing a path for it. */}
                    {selected.file_path ?? "no indexed source"}
                  </span>
                  <span className="neighbour-note">
                    {selected.symbol_count} symbols · imported by {selected.depended_on_by} ·
                    imports {selected.depends_on}
                  </span>
                </div>
              ) : (
                <p className="neighbour-note">Select a module to see what it holds.</p>
              )}
            </>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
