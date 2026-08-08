"""Tests for ``graph_to_adjacency`` — JSONB sidecar shape Phase 2 will read."""

from __future__ import annotations

from textwrap import dedent

from repopilot_ingestion.graph import ModuleSource, build_graph, graph_to_adjacency


def _src(text: str) -> str:
    return dedent(text).lstrip()


def test_adjacency_has_all_edge_directions() -> None:
    modules = [
        ModuleSource(
            module="pkg.mod",
            rel_path="pkg/mod.py",
            source=_src(
                """
                import json

                class Base:
                    pass

                class Child(Base):
                    def use(self):
                        return json.loads('{}')
                """
            ),
        )
    ]
    adj = graph_to_adjacency(build_graph(modules))

    # call edge — both directions
    assert "json.loads" in adj["pkg.mod.Child.use"]["calls"]
    assert "pkg.mod.Child.use" in adj["json.loads"]["called_by"]

    # import edge
    assert "json" in adj["pkg.mod"]["imports"]
    assert "pkg.mod" in adj["json"]["imported_by"]

    # inherit edge
    assert "pkg.mod.Base" in adj["pkg.mod.Child"]["inherits"]
    assert "pkg.mod.Child" in adj["pkg.mod.Base"]["inherited_by"]


def test_adjacency_keys_are_stable() -> None:
    """Every node carries all six bucket keys, even when empty.

    Phase 2's deterministic tools layer relies on this — no key checks.
    """
    modules = [
        ModuleSource(
            module="m",
            rel_path="m.py",
            source="x = 1\n",
        )
    ]
    adj = graph_to_adjacency(build_graph(modules))
    expected_keys = {
        "calls",
        "called_by",
        "imports",
        "imported_by",
        "inherits",
        "inherited_by",
        "defines",
        "defined_by",
    }
    for node, buckets in adj.items():
        assert set(buckets) == expected_keys, f"node {node!r} missing keys"
        for bucket in buckets.values():
            assert isinstance(bucket, list)
