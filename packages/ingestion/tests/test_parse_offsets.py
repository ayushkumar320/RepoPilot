"""Byte-vs-character offset regression tests for the tree-sitter parser.

tree-sitter reports ``start_byte``/``end_byte`` against the UTF-8 buffer it
parsed. Slicing the decoded ``str`` with those offsets shifts every span after
a file's first non-ASCII character, which silently corrupts ``ParsedSymbol``
names — and ``chunks.symbol`` is the only join from a code-graph node back to a
``file:line``, so a corrupted name is a claim that loses its source ref.

This repo's own comment style (em-dashes, box-drawing rules) puts non-ASCII in
most files, so the bug fired on the large majority of real symbols.
"""

from __future__ import annotations

from pathlib import Path

from repopilot_ingestion.parse import parse_file

# Each em-dash is 3 UTF-8 bytes but 1 character, so by the first def the byte
# offset already leads the character offset by well over a symbol's width.
_NON_ASCII_SOURCE = '''\
"""Module docstring — with an em-dash, and another — here.

Notes — these bullets exist purely to widen the byte/char gap:
  • first
  • second
"""

# ── section rule ────────────────────────────────────────────────────────────


def coerce_ref(value: str) -> str:
    """Docstring — also non-ASCII."""
    return value


class Widget:
    """A class — with an em-dash docstring."""

    def render(self) -> str:
        return "ok"
'''


def _write(tmp_path: Path, name: str, body: str) -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def test_symbol_names_survive_non_ascii(tmp_path: Path) -> None:
    """Names must be exact, not shifted slices like 'oerce_ref(v'."""
    parsed = parse_file(_write(tmp_path, "mod.py", _NON_ASCII_SOURCE), module="pkg.mod")
    names = {s.name for s in parsed.symbols}
    assert names == {"coerce_ref", "Widget", "render"}


def test_qualified_names_survive_non_ascii(tmp_path: Path) -> None:
    parsed = parse_file(_write(tmp_path, "mod.py", _NON_ASCII_SOURCE), module="pkg.mod")
    quals = {s.qualified_name for s in parsed.symbols}
    assert quals == {"pkg.mod.coerce_ref", "pkg.mod.Widget", "pkg.mod.Widget.render"}


def test_signature_survives_non_ascii(tmp_path: Path) -> None:
    """_signature slices between two nodes, so it carried the same bug."""
    parsed = parse_file(_write(tmp_path, "mod.py", _NON_ASCII_SOURCE), module="pkg.mod")
    fn = next(s for s in parsed.symbols if s.name == "coerce_ref")
    assert fn.signature == "def coerce_ref(value: str) -> str:"


def test_docstring_survives_non_ascii(tmp_path: Path) -> None:
    parsed = parse_file(_write(tmp_path, "mod.py", _NON_ASCII_SOURCE), module="pkg.mod")
    fn = next(s for s in parsed.symbols if s.name == "coerce_ref")
    assert fn.docstring == "Docstring — also non-ASCII."


def test_imports_survive_non_ascii(tmp_path: Path) -> None:
    """Import edges feed the graph's alias map, so they must not shift either."""
    source = "# héllo — a non-ASCII comment\nimport os\nfrom pathlib import Path as P\n"
    parsed = parse_file(_write(tmp_path, "imp.py", source), module="pkg.imp")
    modules = {e.module for e in parsed.imports}
    assert "os" in modules
    assert "pathlib" in modules
    from_edge = next(e for e in parsed.imports if e.module == "pathlib")
    assert from_edge.names == ("Path",)
    assert from_edge.aliases == {"Path": "P"}


def test_ascii_only_file_is_unaffected(tmp_path: Path) -> None:
    """The pure-ASCII path is where byte and char offsets agree; keep it green."""
    source = "def plain(value):\n    return value\n"
    parsed = parse_file(_write(tmp_path, "plain.py", source), module="pkg.plain")
    assert [s.name for s in parsed.symbols] == ["plain"]
    assert parsed.symbols[0].signature == "def plain(value):"


def test_class_bases_and_methods_survive_non_ascii(tmp_path: Path) -> None:
    source = (
        '"""Header — em-dash."""\n\n'
        "class Base:\n    pass\n\n\n"
        "class Child(Base):\n"
        '    """Child — docstring."""\n\n'
        "    def method_one(self):\n        return 1\n"
    )
    parsed = parse_file(_write(tmp_path, "cls.py", source), module="pkg.cls")
    child = next(s for s in parsed.symbols if s.name == "Child")
    assert child.bases == ("Base",)
    assert child.method_names == ("method_one",)
