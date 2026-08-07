"use client";

import { ArrowsOutSimple, CaretDown, CaretRight, Prohibit } from "@phosphor-icons/react";
import { useCallback, useState } from "react";

import {
  ApiError,
  api,
  type GraphEdgeKind,
  type GraphNeighbour,
  type GraphNeighboursResponse,
} from "../lib/api/generated";

/** Reading order: what this symbol does and who needs it, then imports. */
const EDGE_ORDER: GraphEdgeKind[] = [
  "calls",
  "called_by",
  "inherits",
  "inherited_by",
  "imports",
  "imported_by",
];

const EDGE_LABEL: Record<GraphEdgeKind, string> = {
  calls: "Calls",
  called_by: "Called by",
  inherits: "Inherits",
  inherited_by: "Inherited by",
  imports: "Imports",
  imported_by: "Imported by",
};

type LoadState =
  | { phase: "idle" }
  | { phase: "loading" }
  | { phase: "error"; message: string }
  | { phase: "loaded"; data: GraphNeighboursResponse };

function groupByEdge(neighbours: GraphNeighbour[]): [GraphEdgeKind, GraphNeighbour[]][] {
  return EDGE_ORDER.map(
    (edge) => [edge, neighbours.filter((n) => n.edge === edge)] as [GraphEdgeKind, GraphNeighbour[]],
  ).filter(([, items]) => items.length > 0);
}

/** One neighbour. Expands to show its source, but only if we actually have one. */
function NeighbourRow({ neighbour }: { neighbour: GraphNeighbour }) {
  const [source, setSource] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggle = useCallback(async () => {
    if (open) {
      setOpen(false);
      return;
    }
    setOpen(true);
    if (source !== null || !neighbour.chunk_id) return;
    try {
      const chunk = await api.getChunk(neighbour.chunk_id);
      setSource(chunk.content);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not load this source.");
    }
  }, [open, source, neighbour.chunk_id]);

  // Nothing to open: say why rather than offering a dead control. An
  // unresolved symbol has no file:line, and inventing one is exactly what
  // this product does not do.
  if (!neighbour.resolved || !neighbour.ref) {
    return (
      <li className="neighbour-row" data-unresolved="true">
        <span className="neighbour-icon" aria-hidden="true">
          <Prohibit size={15} />
        </span>
        <span className="neighbour-body">
          <span className="neighbour-name">{neighbour.label}</span>
          <span className="neighbour-note">
            {neighbour.external ? "outside this repository" : "no indexed source"}
          </span>
        </span>
      </li>
    );
  }

  return (
    <li className="neighbour-row">
      <button
        type="button"
        className="neighbour-toggle"
        aria-expanded={open}
        onClick={() => void toggle()}
      >
        <span className="neighbour-icon" aria-hidden="true">
          {open ? <CaretDown size={15} /> : <CaretRight size={15} />}
        </span>
        <span className="neighbour-body">
          <span className="neighbour-name">{neighbour.label}</span>
          <span className="neighbour-ref">
            {neighbour.ref.file_path}:{neighbour.ref.start_line}-{neighbour.ref.end_line}
          </span>
        </span>
      </button>
      {open ? (
        <div className="neighbour-source">
          {error ? (
            <p className="neighbour-note">{error}</p>
          ) : source === null ? (
            <p className="neighbour-note">Loading source…</p>
          ) : (
            <pre>
              <code>{source}</code>
            </pre>
          )}
        </div>
      ) : null}
    </li>
  );
}

export function GraphNeighbours({ repoId, symbol }: { repoId: string; symbol: string }) {
  const [expanded, setExpanded] = useState(false);
  const [state, setState] = useState<LoadState>({ phase: "idle" });

  const open = useCallback(async () => {
    if (expanded) {
      setExpanded(false);
      return;
    }
    setExpanded(true);
    if (state.phase !== "idle") return;
    setState({ phase: "loading" });
    try {
      setState({ phase: "loaded", data: await api.getGraphNeighbours(repoId, symbol) });
    } catch (caught) {
      setState({
        phase: "error",
        message:
          caught instanceof ApiError ? caught.message : "Could not load related code right now.",
      });
    }
  }, [expanded, state.phase, repoId, symbol]);

  return (
    <div className="neighbours">
      <button
        type="button"
        className="neighbours-toggle"
        aria-expanded={expanded}
        onClick={() => void open()}
      >
        <ArrowsOutSimple size={15} aria-hidden="true" />
        Related code
      </button>

      {expanded ? (
        <div className="neighbours-body">
          {state.phase === "loading" ? <p className="neighbour-note">Reading the code graph…</p> : null}
          {state.phase === "error" ? <p className="neighbour-note">{state.message}</p> : null}
          {state.phase === "loaded" ? <NeighbourList data={state.data} /> : null}
        </div>
      ) : null}
    </div>
  );
}

function NeighbourList({ data }: { data: GraphNeighboursResponse }) {
  // A repo with no Python has no graph. Say that plainly — an empty list here
  // reads as a broken feature rather than one that does not apply.
  if (!data.available) {
    return (
      <p className="neighbour-note">
        No call graph for this repository. Dependency graphs are built from Python source.
      </p>
    );
  }
  if (!data.found || data.neighbours.length === 0) {
    return <p className="neighbour-note">Nothing else in the graph references this symbol.</p>;
  }

  return (
    <>
      {groupByEdge(data.neighbours).map(([edge, items]) => (
        <div className="neighbour-group" key={edge}>
          <div className="neighbour-group-label">{EDGE_LABEL[edge]}</div>
          <ul>
            {items.map((n) => (
              <NeighbourRow key={`${n.edge}:${n.symbol}`} neighbour={n} />
            ))}
          </ul>
        </div>
      ))}
      {data.truncated ? (
        <p className="neighbour-note">
          Showing {data.neighbours.length} of {data.total}.
        </p>
      ) : null}
    </>
  );
}
