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


def test_instance_attribute_type_resolves_the_call() -> None:
    """``self.x.y()`` binds through x's declared type, not just ``self.y()``."""
    modules = [
        ModuleSource(
            module="pkg.mod",
            rel_path="pkg/mod.py",
            source=_src(
                """
                class Transport:
                    def handle(self):
                        return 1

                class Client:
                    def __init__(self):
                        self._transport = Transport()

                    def send(self):
                        return self._transport.handle()
                """
            ),
        )
    ]
    g = build_graph(modules)
    assert g.has_edge("pkg.mod.Client.send", "pkg.mod.Transport.handle")


def test_attribute_type_from_annotation_survives_optional_and_quotes() -> None:
    """``T | None`` and a quoted forward reference both name T."""
    modules = [
        ModuleSource(
            module="pkg.mod",
            rel_path="pkg/mod.py",
            source=_src(
                """
                class Transport:
                    def handle(self):
                        return 1

                class Client:
                    _t: "Transport | None" = None

                    def send(self):
                        return self._t.handle()
                """
            ),
        )
    ]
    g = build_graph(modules)
    assert g.has_edge("pkg.mod.Client.send", "pkg.mod.Transport.handle")


def test_local_variable_type_comes_from_the_declared_return() -> None:
    """The two-hop shape: local = self.pick(); local.method()."""
    modules = [
        ModuleSource(
            module="pkg.mod",
            rel_path="pkg/mod.py",
            source=_src(
                """
                class Transport:
                    def handle(self):
                        return 1

                class Client:
                    def _pick(self) -> Transport:
                        return Transport()

                    def send(self):
                        transport = self._pick()
                        return transport.handle()
                """
            ),
        )
    ]
    g = build_graph(modules)
    assert nx.has_path(g, "pkg.mod.Client.send", "pkg.mod.Transport.handle")


def test_untyped_attribute_yields_no_edge() -> None:
    """No declared type means no guess. Inventing here invents a symbol."""
    modules = [
        ModuleSource(
            module="pkg.mod",
            rel_path="pkg/mod.py",
            source=_src(
                """
                class Client:
                    def __init__(self, thing):
                        self._thing = thing

                    def send(self):
                        return self._thing.handle()
                """
            ),
        )
    ]
    g = build_graph(modules)
    assert not [n for n in g.nodes if n.endswith(".handle")]


def test_a_member_no_file_defines_is_not_invented() -> None:
    """The receiver's type is ours; ``close`` is inherited from a third party.

    Emitting ``pkg.mod.Session.close`` would put a repo-shaped symbol in the
    graph that no file defines, and the panel would offer a dead row.
    """
    modules = [
        ModuleSource(
            module="pkg.mod",
            rel_path="pkg/mod.py",
            source=_src(
                """
                from thirdparty import SessionBase

                class Session(SessionBase):
                    pass

                class Client:
                    def __init__(self):
                        self._session = Session()

                    def stop(self):
                        return self._session.close()
                """
            ),
        )
    ]
    g = build_graph(modules)
    assert "pkg.mod.Session.close" not in g.nodes


def test_a_function_local_import_does_not_bind_file_wide() -> None:
    """Preparing aliases up front must not hoist a name out of its function."""
    modules = [
        ModuleSource(
            module="pkg.mod",
            rel_path="pkg/mod.py",
            source=_src(
                """
                def early():
                    return helper()

                def late():
                    from other import helper

                    return helper()
                """
            ),
        )
    ]
    g = build_graph(modules)
    assert not g.has_edge("pkg.mod.early", "other.helper")
    assert g.has_edge("pkg.mod.late", "other.helper")
