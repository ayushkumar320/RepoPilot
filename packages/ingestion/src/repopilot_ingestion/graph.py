"""NetworkX dependency graph builder.

Edges (Phase 1, deterministic — the LLM never invents these):

* ``calls``   — function/method A calls function/method B (resolved via a
                scope-aware AST walk over Python's own ``ast`` module)
* ``imports`` — file F imports symbol S (qualified)
* ``inherits``— class C extends class D (qualified)

Unresolvable patterns (decorators that rewrite signatures, ``getattr``,
dynamic dispatch) **log a warning** and are dropped. We never invent edges.

The graph is built from the source on disk (not from tree-sitter) so we get
Python's well-tested ``ast`` semantics for scoping. tree-sitter remains the
source of truth for *line spans* — its concrete-syntax view is more reliable
for chunk boundaries — but ``ast`` is the right tool for binding names.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

import networkx as nx
import structlog

log = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ModuleSource:
    """Resolved module info handed to the graph builder."""

    module: str  # dotted module path, e.g. "httpx._client"
    rel_path: str  # repo-relative path string
    source: str  # file contents


def build_graph(modules: Iterable[ModuleSource]) -> nx.DiGraph[str]:
    """Build a directed graph from a collection of Python module sources.

    Nodes are qualified symbol names (modules, classes, functions, methods).
    Every node has a ``kind`` attribute. Edges carry a ``type`` attribute
    drawn from ``{"calls", "imports", "inherits"}``.
    """
    graph: nx.DiGraph[str] = nx.DiGraph()

    # Pass 1: collect defined symbols per module so call/inherit resolution
    # in pass 2 has the full universe of names available.
    defined: dict[str, set[str]] = defaultdict(set)
    modules_list = list(modules)
    parsed_trees: dict[str, ast.Module] = {}

    for mod in modules_list:
        try:
            tree = ast.parse(mod.source, filename=mod.rel_path)
        except SyntaxError as exc:
            log.warning(
                "graph.parse_error",
                module=mod.module,
                path=mod.rel_path,
                error=str(exc),
            )
            continue
        parsed_trees[mod.module] = tree
        graph.add_node(mod.module, kind="module", path=mod.rel_path)
        for sym in _walk_definitions(tree, mod.module):
            graph.add_node(sym.qual, kind=sym.kind, path=mod.rel_path)
            defined[mod.module].add(sym.qual)

    # Pass 2: edges. We need the alias map per module, so we walk the AST
    # one more time per file rather than threading it through pass 1.
    for mod in modules_list:
        mod_tree = parsed_trees.get(mod.module)
        if mod_tree is None:
            continue
        is_package = mod.rel_path.replace("\\", "/").rsplit("/", 1)[-1] == "__init__.py"
        package = mod.module if is_package else mod.module.rpartition(".")[0]
        resolver = _Resolver(module=mod.module, defined=defined, package=package)
        resolver.visit(mod_tree)

        for src, dst in resolver.imports:
            graph.add_edge(src, dst, type="imports")
        for src, dst in resolver.inherits:
            graph.add_edge(src, dst, type="inherits")
        for src, dst in resolver.calls:
            graph.add_edge(src, dst, type="calls")

    return graph


def graph_to_adjacency(graph: nx.DiGraph[str]) -> dict[str, dict[str, list[str]]]:
    """Serialise to the JSONB sidecar shape stored in ``graph_adjacency``.

    ``{node: {calls: [...], called_by: [...], imports: [...], inherits: [...]}}``.
    Keys are stable so the deterministic tools layer (Phase 2) can read them
    without further parsing.
    """
    out: dict[str, dict[str, list[str]]] = {}
    for node in graph.nodes:
        out[node] = {
            "calls": [],
            "called_by": [],
            "imports": [],
            "imported_by": [],
            "inherits": [],
            "inherited_by": [],
        }
    for src, dst, data in graph.edges(data=True):
        etype = str(data.get("type", ""))
        if etype == "calls":
            out[src]["calls"].append(dst)
            out[dst]["called_by"].append(src)
        elif etype == "imports":
            out[src]["imports"].append(dst)
            out[dst]["imported_by"].append(src)
        elif etype == "inherits":
            out[src]["inherits"].append(dst)
            out[dst]["inherited_by"].append(src)
    return out


# ── internals ───────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class _DefSymbol:
    qual: str
    kind: str


def _walk_definitions(tree: ast.Module, module: str) -> list[_DefSymbol]:
    out: list[_DefSymbol] = []

    def visit(node: ast.AST, parent_qual: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qual = f"{parent_qual}.{child.name}"
                kind = "method" if parent_qual != module else "function"
                # Treat nested defs under classes as methods, otherwise functions.
                out.append(_DefSymbol(qual=qual, kind=kind))
                visit(child, qual)
            elif isinstance(child, ast.ClassDef):
                qual = f"{parent_qual}.{child.name}"
                out.append(_DefSymbol(qual=qual, kind="class"))
                visit(child, qual)

    visit(tree, module)
    return out


class _Resolver(ast.NodeVisitor):
    """Walk one module and emit edges into typed lists.

    Scope tracking is minimal but sufficient for v1:

    * ``aliases`` maps a local name -> dotted target ("requests" -> "requests",
      "rq" -> "requests" for ``import requests as rq``). For ``from x import y``
      this is "y" -> "x.y".
    * ``current_qual`` is the qualified name of the surrounding def/class,
      used to attribute call edges to the right node.
    """

    def __init__(self, *, module: str, defined: dict[str, set[str]], package: str = "") -> None:
        super().__init__()
        self.module = module
        # The package a relative import counts levels from. For ``a/b/__init__.py``
        # that is ``a.b`` itself; for ``a/b/c.py`` it is ``a.b``.
        self.package = package
        self.defined = defined
        self.aliases: dict[str, str] = {}
        self.self_class_stack: list[str] = []
        self.current_qual_stack: list[str] = [module]
        self.calls: list[tuple[str, str]] = []
        self.imports: list[tuple[str, str]] = []
        self.inherits: list[tuple[str, str]] = []

    # ── current scope ──
    @property
    def current_qual(self) -> str:
        return self.current_qual_stack[-1]

    @property
    def in_method(self) -> bool:
        return bool(self.self_class_stack)

    # ── imports ──
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            target = alias.name
            local = alias.asname or alias.name.split(".")[0]
            self.aliases[local] = target
            self.imports.append((self.module, target))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        mod = node.module or ""
        if node.level:
            # Relative imports are how a package refers to itself, so skipping
            # them dropped most intra-repo edges AND starved the alias map that
            # resolves cross-module calls. Level 1 is this module's own package,
            # each extra level climbs one more.
            base = self.package
            for _ in range(node.level - 1):
                base = base.rpartition(".")[0]
            if not base:
                log.debug(
                    "graph.relative_import_above_root",
                    module=self.module,
                    level=node.level,
                    target=mod,
                )
                return
            mod = f"{base}.{mod}" if mod else base
        for alias in node.names:
            if alias.name == "*":
                log.debug("graph.star_import_skipped", module=self.module, target=mod)
                continue
            target = f"{mod}.{alias.name}" if mod else alias.name
            local = alias.asname or alias.name
            self.aliases[local] = target
            self.imports.append((self.module, target))

    # ── classes ──
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qual = f"{self.current_qual}.{node.name}"
        for base in node.bases:
            resolved = self._resolve_name(base)
            if resolved is not None:
                self.inherits.append((qual, resolved))
        self.current_qual_stack.append(qual)
        self.self_class_stack.append(qual)
        self.generic_visit(node)
        self.self_class_stack.pop()
        self.current_qual_stack.pop()

    # ── functions / methods ──
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function_like(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function_like(node)

    def _visit_function_like(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qual = f"{self.current_qual}.{node.name}"
        self.current_qual_stack.append(qual)
        self.generic_visit(node)
        self.current_qual_stack.pop()

    # ── calls ──
    def visit_Call(self, node: ast.Call) -> None:
        target = self._resolve_call(node.func)
        if target is not None:
            self.calls.append((self.current_qual, target))
        else:
            log.debug(
                "graph.unresolved_call",
                module=self.module,
                caller=self.current_qual,
                shape=type(node.func).__name__,
            )
        self.generic_visit(node)

    # ── name resolution ──
    def _resolve_name(self, node: ast.AST) -> str | None:
        """Resolve an ``ast.Name`` or ``ast.Attribute`` to a dotted qualified name."""
        if isinstance(node, ast.Name):
            if node.id in self.aliases:
                return self.aliases[node.id]
            # Same-module reference: bind to `module.name` if defined here.
            same_module_qual = f"{self.module}.{node.id}"
            if same_module_qual in self.defined.get(self.module, set()):
                return same_module_qual
            return None
        if isinstance(node, ast.Attribute):
            base = self._resolve_name(node.value)
            if base is None:
                return None
            return f"{base}.{node.attr}"
        return None

    def _resolve_call(self, func: ast.AST) -> str | None:
        # self.method(...) — bind to the enclosing class.
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "self"
            and self.in_method
        ):
            return f"{self.self_class_stack[-1]}.{func.attr}"
        return self._resolve_name(func)


__all__ = ["ModuleSource", "build_graph", "graph_to_adjacency"]
