"""Graph-builder tests — call / import / inherit edges from a synthetic repo."""

from __future__ import annotations

from textwrap import dedent

import networkx as nx

from repopilot_ingestion.graph import ModuleSource, build_graph


def _src(text: str) -> str:
    return dedent(text).lstrip()


def test_self_method_calls_resolve_to_enclosing_class() -> None:
    modules = [
        ModuleSource(
            module="pkg.mod",
            rel_path="pkg/mod.py",
            source=_src(
                """
                class A:
                    def one(self):
                        return self.two()

                    def two(self):
                        return 1
                """
            ),
        )
    ]
    g = build_graph(modules)
    assert g.has_edge("pkg.mod.A.one", "pkg.mod.A.two")
    assert g["pkg.mod.A.one"]["pkg.mod.A.two"]["type"] == "calls"


def test_aliased_import_resolves_to_canonical_target() -> None:
    modules = [
        ModuleSource(
            module="pkg.mod",
            rel_path="pkg/mod.py",
            source=_src(
                """
                import requests as rq

                def hit():
                    return rq.get('https://x')
                """
            ),
        )
    ]
    g = build_graph(modules)
    assert g.has_edge("pkg.mod", "requests")
    assert g["pkg.mod"]["requests"]["type"] == "imports"
    assert g.has_edge("pkg.mod.hit", "requests.get")


def test_from_import_with_alias() -> None:
    modules = [
        ModuleSource(
            module="pkg.mod",
            rel_path="pkg/mod.py",
            source=_src(
                """
                from json import loads as j_loads

                def parse(s):
                    return j_loads(s)
                """
            ),
        )
    ]
    g = build_graph(modules)
    assert g.has_edge("pkg.mod.parse", "json.loads")


def test_inheritance_edges() -> None:
    modules = [
        ModuleSource(
            module="m",
            rel_path="m.py",
            source=_src(
                """
                class Base:
                    pass

                class Child(Base):
                    pass
                """
            ),
        )
    ]
    g = build_graph(modules)
    assert g.has_edge("m.Child", "m.Base")
    assert g["m.Child"]["m.Base"]["type"] == "inherits"


def test_path_via_graph_traversal() -> None:
    """Multi-module path: A.run -> B.helper. Phase 2's tools build on this."""
    modules = [
        ModuleSource(
            module="a",
            rel_path="a.py",
            source=_src(
                """
                from b import helper

                def run():
                    return helper()
                """
            ),
        ),
        ModuleSource(
            module="b",
            rel_path="b.py",
            source=_src(
                """
                def helper():
                    return 42
                """
            ),
        ),
    ]
    g = build_graph(modules)
    assert nx.has_path(g, "a.run", "b.helper")
