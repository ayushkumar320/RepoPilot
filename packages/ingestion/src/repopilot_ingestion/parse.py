"""tree-sitter parser → typed ``ParsedFile`` with function/class spans.

Phase 1 only cares about a small slice of the Python grammar:

* module-level imports (``import x``, ``from a import b as c``)
* top-level and nested function definitions (incl. methods, ``async def``)
* class definitions, with their docstring and method *names*
* base-class names on class definitions

Anything richer (decorators, type aliases, attribute assignments) is left for
later phases — Phase 1's job is to feed the chunker and the graph builder, and
those two only need symbols + line spans + the import / inheritance edges that
the AST itself surfaces deterministically.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import tree_sitter_python
from tree_sitter import Language, Node, Parser

SymbolKind = Literal["function", "class", "method"]

_LANGUAGE = Language(tree_sitter_python.language())
_PARSER = Parser(_LANGUAGE)


@dataclass(frozen=True, slots=True)
class ImportEdge:
    """One ``import`` or ``from … import …`` line.

    ``module`` is the dotted module path; ``names`` is the imported symbol
    list. For ``import x as y`` the alias is recorded in ``aliases[name]``.
    """

    module: str
    names: tuple[str, ...]
    aliases: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ParsedSymbol:
    """A function, class, or method definition with exact line spans (1-based)."""

    name: str
    qualified_name: str
    kind: SymbolKind
    start_line: int
    end_line: int
    docstring: str | None
    # For classes: dotted base names appearing in the parens.
    bases: tuple[str, ...] = ()
    # For classes: child method names in source order.
    method_names: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ParsedFile:
    path: Path
    module: str  # dotted module path (e.g. "pkg.mod"); "" for unknown
    source: str
    line_count: int
    imports: tuple[ImportEdge, ...]
    symbols: tuple[ParsedSymbol, ...]


def parse_file(path: Path, *, module: str = "") -> ParsedFile:
    source = path.read_text(encoding="utf-8", errors="replace")
    tree = _PARSER.parse(source.encode("utf-8"))
    root = tree.root_node

    imports = tuple(_extract_imports(root, source))
    symbols = tuple(_extract_symbols(root, source, parent_qual=module))

    return ParsedFile(
        path=path,
        module=module,
        source=source,
        line_count=source.count("\n") + 1,
        imports=imports,
        symbols=symbols,
    )


# ── internals ───────────────────────────────────────────────────────────────


def _text(node: Node, source: str) -> str:
    return source[node.start_byte : node.end_byte]


def _line_span(node: Node) -> tuple[int, int]:
    """Convert tree-sitter's 0-based rows to inclusive 1-based line numbers."""
    return node.start_point[0] + 1, node.end_point[0] + 1


def _extract_imports(root: Node, source: str) -> list[ImportEdge]:
    out: list[ImportEdge] = []
    for child in root.children:
        if child.type == "import_statement":
            for dotted, alias in _walk_dotted_aliases(child, source):
                edge = ImportEdge(module=dotted, names=(dotted,))
                if alias is not None:
                    edge.aliases[dotted] = alias
                out.append(edge)
        elif child.type == "import_from_statement":
            out.extend(_parse_from_import(child, source))
    return out


def _walk_dotted_aliases(
    node: Node, source: str
) -> list[tuple[str, str | None]]:
    """Yield ``(dotted_module, alias_or_None)`` pairs from an ``import`` node."""
    out: list[tuple[str, str | None]] = []
    for child in node.children:
        if child.type == "dotted_name":
            out.append((_text(child, source), None))
        elif child.type == "aliased_import":
            dotted = child.child_by_field_name("name")
            alias = child.child_by_field_name("alias")
            if dotted is not None and alias is not None:
                out.append((_text(dotted, source), _text(alias, source)))
    return out


def _parse_from_import(node: Node, source: str) -> list[ImportEdge]:
    module_node = node.child_by_field_name("module_name")
    module = _text(module_node, source) if module_node is not None else ""

    names: list[str] = []
    aliases: dict[str, str] = {}
    for child in node.children:
        if child.type == "dotted_name" and child is not module_node:
            names.append(_text(child, source))
        elif child.type == "aliased_import":
            inner = child.child_by_field_name("name")
            alias = child.child_by_field_name("alias")
            if inner is not None and alias is not None:
                name = _text(inner, source)
                names.append(name)
                aliases[name] = _text(alias, source)
        elif child.type == "wildcard_import":
            names.append("*")

    if not names:
        return []
    return [ImportEdge(module=module, names=tuple(names), aliases=aliases)]


def _extract_symbols(
    node: Node, source: str, *, parent_qual: str
) -> list[ParsedSymbol]:
    out: list[ParsedSymbol] = []
    for child in _iter_block_children(node):
        if child.type in {"function_definition", "decorated_definition"}:
            fn = _strip_decorator(child)
            if fn is None or fn.type != "function_definition":
                continue
            name_node = fn.child_by_field_name("name")
            if name_node is None:
                continue
            name = _text(name_node, source)
            qual = f"{parent_qual}.{name}" if parent_qual else name
            start, end = _line_span(child)
            out.append(
                ParsedSymbol(
                    name=name,
                    qualified_name=qual,
                    kind="function",
                    start_line=start,
                    end_line=end,
                    docstring=_first_docstring(fn, source),
                )
            )
        elif child.type == "class_definition":
            name_node = child.child_by_field_name("name")
            if name_node is None:
                continue
            name = _text(name_node, source)
            qual = f"{parent_qual}.{name}" if parent_qual else name
            start, end = _line_span(child)
            bases = tuple(_class_base_names(child, source))
            methods = tuple(_class_method_names(child, source))
            out.append(
                ParsedSymbol(
                    name=name,
                    qualified_name=qual,
                    kind="class",
                    start_line=start,
                    end_line=end,
                    docstring=_first_docstring(child, source),
                    bases=bases,
                    method_names=methods,
                )
            )
            # Methods are emitted as independent ``method`` symbols so the
            # chunker can keep their bodies separate from the class chunk.
            body = child.child_by_field_name("body")
            if body is not None:
                for method in _iter_block_children(body):
                    fn = _strip_decorator(method)
                    if fn is None or fn.type != "function_definition":
                        continue
                    mname_node = fn.child_by_field_name("name")
                    if mname_node is None:
                        continue
                    mname = _text(mname_node, source)
                    mstart, mend = _line_span(method)
                    out.append(
                        ParsedSymbol(
                            name=mname,
                            qualified_name=f"{qual}.{mname}",
                            kind="method",
                            start_line=mstart,
                            end_line=mend,
                            docstring=_first_docstring(fn, source),
                        )
                    )
    return out


def _iter_block_children(node: Node) -> Iterator[Node]:
    """Iterate the statements of a module or a class/function body block.

    For module nodes the children are the statements directly; for class /
    function bodies the children sit under a ``block`` node.
    """
    if node.type == "block":
        yield from node.children
        return
    body = node.child_by_field_name("body") if node.type != "module" else None
    if body is not None:
        yield from body.children
    else:
        yield from node.children


def _strip_decorator(node: Node) -> Node | None:
    """Return the underlying ``function_definition`` from a (possibly decorated) node."""
    if node.type == "function_definition":
        return node
    if node.type == "decorated_definition":
        for child in node.children:
            if child.type in {"function_definition", "class_definition"}:
                return child
    return None


def _first_docstring(node: Node, source: str) -> str | None:
    body = node.child_by_field_name("body")
    if body is None:
        return None
    for child in body.children:
        if child.type == "expression_statement":
            inner = child.children[0] if child.children else None
            if inner is not None and inner.type == "string":
                # Strip the surrounding quote tokens by trimming the raw text.
                return _text(inner, source)
        break
    return None


def _class_base_names(node: Node, source: str) -> list[str]:
    superclasses = node.child_by_field_name("superclasses")
    if superclasses is None:
        return []
    out: list[str] = []
    for child in superclasses.children:
        if child.type in {"identifier", "attribute"}:
            out.append(_text(child, source))
    return out


def _class_method_names(node: Node, source: str) -> list[str]:
    body = node.child_by_field_name("body")
    if body is None:
        return []
    names: list[str] = []
    for child in body.children:
        fn = _strip_decorator(child)
        if fn is not None and fn.type == "function_definition":
            name_node = fn.child_by_field_name("name")
            if name_node is not None:
                names.append(_text(name_node, source))
    return names


__all__ = [
    "ImportEdge",
    "ParsedFile",
    "ParsedSymbol",
    "SymbolKind",
    "parse_file",
]
