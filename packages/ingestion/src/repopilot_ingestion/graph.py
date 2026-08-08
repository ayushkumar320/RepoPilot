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
from collections.abc import Callable, Iterable, Iterator
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
    # Every class this repo defines, qualified. Attribute-type inference in
    # pass 2 will only bind to a name in here: a declared type that turns out
    # to be a function, or a third party's class we never parsed, would put a
    # symbol in the graph that no file defines.
    classes: set[str] = set()
    # Every symbol, of any kind. A typed receiver only yields an edge when the
    # member it names is in here.
    symbols: set[str] = set()
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
            symbols.add(sym.qual)
            if sym.kind == "class":
                classes.add(sym.qual)

    # Pass 2: edges. We need the alias map per module, so we walk the AST
    # one more time per file rather than threading it through pass 1.
    for mod in modules_list:
        mod_tree = parsed_trees.get(mod.module)
        if mod_tree is None:
            continue
        is_package = mod.rel_path.replace("\\", "/").rsplit("/", 1)[-1] == "__init__.py"
        package = mod.module if is_package else mod.module.rpartition(".")[0]
        resolver = _Resolver(
            module=mod.module,
            defined=defined,
            package=package,
            classes=classes,
            symbols=symbols,
        )
        resolver.prepare(mod_tree)
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
    * ``attr_types`` maps a class -> its instance attributes' declared types,
      so ``self._transport.handle_request()`` can bind. See
      ``_scan_class_attributes`` for what counts as declared.
    """

    def __init__(
        self,
        *,
        module: str,
        defined: dict[str, set[str]],
        package: str = "",
        classes: set[str] | None = None,
        symbols: set[str] | None = None,
    ) -> None:
        super().__init__()
        self.module = module
        # The package a relative import counts levels from. For ``a/b/__init__.py``
        # that is ``a.b`` itself; for ``a/b/c.py`` it is ``a.b``.
        self.package = package
        self.defined = defined
        self.classes = classes if classes is not None else set()
        self.symbols = symbols if symbols is not None else set()
        self.aliases: dict[str, str] = {}
        self.self_class_stack: list[str] = []
        self.current_qual_stack: list[str] = [module]
        self.attr_types: dict[str, dict[str, str]] = {}
        self.return_types: dict[str, str] = {}
        self.local_types_stack: list[dict[str, str]] = []
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

    # ── preparation ──
    def prepare(self, tree: ast.Module) -> None:
        """Bind names that the edge walk needs *before* it reaches them.

        Two things are only knowable up front. Aliases, because a type
        annotation near the top of a class refers to an import that
        ``generic_visit`` has already passed but a class scan has not; and
        return annotations, because ``x = self.build()`` types ``x`` from a
        method that may be declared further down the file.
        """
        for node in _module_scope_nodes(tree):
            if isinstance(node, ast.Import):
                self._bind_import(node)
            elif isinstance(node, ast.ImportFrom):
                self._bind_import_from(node)
        self._scan_return_types(tree, self.module)

    def _scan_return_types(self, node: ast.AST, parent_qual: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qual = f"{parent_qual}.{child.name}"
                if child.returns is not None:
                    declared = self._resolve_class(child.returns)
                    if declared is not None:
                        self.return_types[qual] = declared
                self._scan_return_types(child, qual)
            elif isinstance(child, ast.ClassDef):
                self._scan_return_types(child, f"{parent_qual}.{child.name}")

    # ── imports ──
    def _bind_import(self, node: ast.Import) -> list[str]:
        targets = []
        for alias in node.names:
            target = alias.name
            local = alias.asname or alias.name.split(".")[0]
            self.aliases[local] = target
            targets.append(target)
        return targets

    def _bind_import_from(self, node: ast.ImportFrom) -> list[str]:
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
                return []
            mod = f"{base}.{mod}" if mod else base
        targets = []
        for alias in node.names:
            if alias.name == "*":
                log.debug("graph.star_import_skipped", module=self.module, target=mod)
                continue
            target = f"{mod}.{alias.name}" if mod else alias.name
            local = alias.asname or alias.name
            self.aliases[local] = target
            targets.append(target)
        return targets

    def visit_Import(self, node: ast.Import) -> None:
        for target in self._bind_import(node):
            self.imports.append((self.module, target))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for target in self._bind_import_from(node):
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
        # Before the bodies, so a method calling through an attribute assigned
        # in a *later* method still resolves.
        self._scan_class_attributes(node, qual)
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
        self.local_types_stack.append(self._scan_local_types(node))
        self.generic_visit(node)
        self.local_types_stack.pop()
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

    # ── declared types ──
    def _scan_class_attributes(self, node: ast.ClassDef, class_qual: str) -> None:
        """Record ``self.<attr>`` types for one class, from *declared* types only.

        1. class-level annotations — ``transport: BaseTransport``
        2. ``self.x: BaseTransport`` anywhere in a method
        3. ``self.x = <expr>`` where the type is declared rather than guessed:
           a constructor call ``self.x = HTTPTransport(...)``, or a call whose
           *return annotation* names a class (``self.x = self._init_transport()``
           declared ``-> BaseTransport``).

        An untyped ``self.x = build()`` is left alone. Guessing there is how a
        graph grows edges to symbols no file defines.
        """
        attrs = self.attr_types.setdefault(class_qual, {})

        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                declared = self._resolve_class(item.annotation)
                if declared is not None:
                    attrs[item.target.id] = declared

        for item in node.body:
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for name, declared in self._declared_assignments(item, _self_attr_name):
                attrs[name] = declared

    def _scan_local_types(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, str]:
        """Local names in one function body whose type is declared.

        Parameter annotations plus the same assignment rules as instance
        attributes. This is what carries the common two-hop shape —
        ``transport = self._transport_for_url(url)`` then
        ``transport.handle_request(...)`` — which is otherwise dropped whole.
        """
        out: dict[str, str] = {}
        args = node.args
        for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs]:
            if arg.annotation is not None:
                declared = self._resolve_class(arg.annotation)
                if declared is not None:
                    out[arg.arg] = declared
        for name, declared in self._declared_assignments(node, _plain_name):
            out[name] = declared
        return out

    def _declared_assignments(
        self, node: ast.AST, pick: Callable[[ast.AST], str | None]
    ) -> Iterator[tuple[str, str]]:
        """Assignments under ``node`` whose target ``pick`` accepts and whose
        right-hand side carries a declared class."""
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.AnnAssign):
                name = pick(stmt.target)
                declared = self._resolve_class(stmt.annotation)
                if name is not None and declared is not None:
                    yield name, declared
            elif isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
                declared = self._call_result_class(stmt.value)
                if declared is None:
                    continue
                for target in stmt.targets:
                    name = pick(target)
                    if name is not None:
                        yield name, declared

    def _call_result_class(self, call: ast.Call) -> str | None:
        """The class a call evaluates to — constructor, or declared return."""
        func = call.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "self"
            and self.self_class_stack
        ):
            return self.return_types.get(f"{self.self_class_stack[-1]}.{func.attr}")
        constructed = self._resolve_class(func)
        if constructed is not None:
            return constructed
        resolved = self._resolve_name(func)
        return None if resolved is None else self.return_types.get(resolved)

    def _resolve_class(self, node: ast.AST) -> str | None:
        """Resolve a type expression, but only to a class this repo defines."""
        resolved = self._resolve_name(_unwrap_optional(node))
        return resolved if resolved is not None and resolved in self.classes else None

    def _attribute_type(self, attr: str) -> str | None:
        if not self.self_class_stack:
            return None
        return self.attr_types.get(self.self_class_stack[-1], {}).get(attr)

    def _local_type(self, name: str) -> str | None:
        for scope in reversed(self.local_types_stack):
            if name in scope:
                return scope[name]
        return None

    def _member(self, owner: str, attr: str) -> str | None:
        """``owner.attr``, but only when some file actually defines it.

        A typed receiver does not make every attribute on it real: the method
        may come from a base class in another package, or from a third party
        we never parsed. Emitting it anyway would put a repo-shaped symbol in
        the graph that no file defines, which is the one thing the builder
        promises not to do.
        """
        member = f"{owner}.{attr}"
        return member if member in self.symbols else None

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
        if isinstance(func, ast.Attribute):
            inner = func.value
            # self.attribute.method(...) — bind through the attribute's type.
            if (
                self.in_method
                and isinstance(inner, ast.Attribute)
                and isinstance(inner.value, ast.Name)
                and inner.value.id == "self"
            ):
                owner = self._attribute_type(inner.attr)
                return None if owner is None else self._member(owner, func.attr)
            # self.method(...) — bind to the enclosing class.
            if self.in_method and isinstance(inner, ast.Name) and inner.id == "self":
                return f"{self.self_class_stack[-1]}.{func.attr}"
            # local.method(...) — bind through the local's declared type.
            if isinstance(inner, ast.Name):
                owner = self._local_type(inner.id)
                if owner is not None:
                    return self._member(owner, func.attr)
        return self._resolve_name(func)


def _module_scope_nodes(tree: ast.Module) -> Iterator[ast.AST]:
    """Statements reachable at module scope, never inside a function body.

    A binding inside ``def`` lives only in that call. Hoisting one to the top
    of the file would let a name a test imports locally resolve in every other
    function too — which is how a "pre-bind the imports" pass quietly grows
    edges that the source does not support. ``if TYPE_CHECKING:`` and ``try:``
    wrappers *are* module scope, so those are followed.
    """
    stack: list[ast.AST] = [tree]
    while stack:
        node = stack.pop()
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            yield child
            stack.append(child)


def _plain_name(target: ast.AST) -> str | None:
    """``foo`` -> ``"foo"``; anything else -> None."""
    return target.id if isinstance(target, ast.Name) else None


def _self_attr_name(target: ast.AST) -> str | None:
    """``self.foo`` -> ``"foo"``; anything else -> None."""
    if (
        isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Name)
        and target.value.id == "self"
    ):
        return target.attr
    return None


def _unwrap_optional(node: ast.AST) -> ast.AST:
    """Strip the wrappers that carry no type of their own.

    ``"Client"`` (a quoted forward reference), ``T | None``, and
    ``Optional[T]`` all name T. Without this, the two ways of spelling a
    nullable attribute — overwhelmingly common on real classes — resolve to
    nothing and the attribute stays untyped.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        try:
            return _unwrap_optional(ast.parse(node.value, mode="eval").body)
        except SyntaxError:
            return node
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left, right = node.left, node.right
        if _is_none(right):
            return _unwrap_optional(left)
        if _is_none(left):
            return _unwrap_optional(right)
        return node
    if isinstance(node, ast.Subscript):
        outer = node.value
        name = outer.attr if isinstance(outer, ast.Attribute) else getattr(outer, "id", None)
        if name == "Optional":
            return _unwrap_optional(node.slice)
    return node


def _is_none(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


__all__ = ["ModuleSource", "build_graph", "graph_to_adjacency"]
