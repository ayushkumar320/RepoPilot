"""Contract for the module dependency map rollup.

The map is the symbol graph seen from further away: one box per module, one
arrow per real intra-repo import. The rules it must not break:

* **Only this repository.** An import of `os` or `httpx` is a real edge in the
  symbol graph and tells a reader nothing about how *this* codebase is laid
  out. Drawing every third-party target is what turns a map into a hairball.
* **Longest prefix owns the symbol.** `flask.json` and `flask.json.provider`
  are both modules; a symbol in the latter must not be attributed to the
  former.
* **Truncation is stated, never silent.** A scoped map reports the true totals
  so the UI can say "showing 40 of 210", and drops edges whose endpoints were
  scoped out rather than drawing a line into nothing.
"""

from __future__ import annotations

from repopilot_api.services import _owning_module, _rollup_modules


def _owners(*names: str) -> dict[str, tuple[str | None, str | None, int]]:
    return {name: (f"{name.replace('.', '/')}.py", f"chunk-{name}", 0) for name in names}


def _adjacency(
    imports: dict[str, list[str]], *, also: tuple[str, ...] = ()
) -> dict[str, dict[str, list[str]]]:
    """Adjacency shaped like the real sidecar.

    `graph_to_adjacency` writes a key for *every* node, so a module that
    imports nothing is still present with empty buckets. Fixtures that list
    only import sources are not what production produces, and the rollup now
    reads key-presence as "this module is Python", so the difference matters.
    """
    out = {name: {"imports": list(targets)} for name, targets in imports.items()}
    for name in also:
        out.setdefault(name, {"imports": []})
    return out


def test_longest_matching_prefix_owns_the_symbol() -> None:
    names = sorted(["flask.json", "flask.json.provider", "flask"], key=len, reverse=True)
    assert _owning_module("flask.json.provider.JSONProvider", names) == "flask.json.provider"
    assert _owning_module("flask.json.dumps", names) == "flask.json"
    assert _owning_module("flask.Flask", names) == "flask"


def test_a_similar_name_is_not_a_prefix_match() -> None:
    """`flask_login` starts with `flask` as text but is a different package."""
    assert _owning_module("flask_login.LoginManager", ["flask"]) is None
    assert _owning_module("flaskish", ["flask"]) is None


def test_third_party_targets_produce_no_edge() -> None:
    adjacency = _adjacency(
        {"pkg.web": ["pkg.core.run", "os.path.join", "httpx.Client"]}, also=("pkg.core",)
    )
    result = _rollup_modules(adjacency, _owners("pkg.web", "pkg.core"), limit=50)
    assert [(e.source, e.target) for e in result.edges] == [("pkg.web", "pkg.core")]
    assert result.total_edges == 1


def test_a_module_importing_from_itself_is_not_a_dependency() -> None:
    adjacency = _adjacency({"pkg.core": ["pkg.core.helper"]})
    result = _rollup_modules(adjacency, _owners("pkg.core"), limit=50)
    assert result.edges == []


def test_parallel_imports_of_one_module_collapse_to_a_single_edge() -> None:
    """Three symbols from one module is one dependency, not three arrows."""
    adjacency = _adjacency(
        {"pkg.web": ["pkg.core.a", "pkg.core.b", "pkg.core.c"]}, also=("pkg.core",)
    )
    result = _rollup_modules(adjacency, _owners("pkg.web", "pkg.core"), limit=50)
    assert len(result.edges) == 1
    assert next(m for m in result.modules if m.symbol == "pkg.web").depends_on == 1
    assert next(m for m in result.modules if m.symbol == "pkg.core").depended_on_by == 1


def test_no_graph_rows_reads_as_unavailable_not_as_an_empty_map() -> None:
    """A repo with no Python must not render as a map that drew nothing."""
    assert _rollup_modules({}, {}, limit=50).available is False


def test_scoping_keeps_the_busiest_and_states_the_true_totals() -> None:
    # hub is imported by three modules; the leaves touch nothing else.
    adjacency = _adjacency(
        {
            "pkg.a": ["pkg.hub.x"],
            "pkg.b": ["pkg.hub.x"],
            "pkg.c": ["pkg.hub.x"],
            "pkg.lonely": [],
        },
        also=("pkg.hub",),
    )
    owners = _owners("pkg.a", "pkg.b", "pkg.c", "pkg.hub", "pkg.lonely")
    result = _rollup_modules(adjacency, owners, limit=2)

    assert result.truncated is True
    assert result.total_modules == 5
    assert result.total_edges == 3
    # The hub has the highest total degree, so it survives scoping.
    assert "pkg.hub" in {m.symbol for m in result.modules}
    assert len(result.modules) == 2


def test_an_edge_to_a_scoped_out_module_is_dropped_not_dangled() -> None:
    adjacency = _adjacency({"pkg.a": ["pkg.hub.x"], "pkg.b": ["pkg.hub.x"]}, also=("pkg.hub",))
    owners = _owners("pkg.a", "pkg.b", "pkg.hub")
    result = _rollup_modules(adjacency, owners, limit=2)

    kept = {m.symbol for m in result.modules}
    for edge in result.edges:
        assert edge.source in kept and edge.target in kept
    # The count still reports every edge the repo really has.
    assert result.total_edges == 2


def test_degree_counts_modules_not_imported_symbols() -> None:
    """`depends_on` answers "how many modules does this need", not "how many
    names does it pull in" — the second is a property of import style."""
    adjacency = _adjacency(
        {"pkg.web": ["pkg.core.a", "pkg.core.b", "pkg.util.c"]},
        also=("pkg.core", "pkg.util"),
    )
    result = _rollup_modules(adjacency, _owners("pkg.web", "pkg.core", "pkg.util"), limit=50)
    web = next(m for m in result.modules if m.symbol == "pkg.web")
    assert web.depends_on == 2


def test_non_python_files_are_not_modules() -> None:
    """README.md and requirements.txt are stored with `kind = 'module'` by the
    generic chunker, but they are not part of any dependency structure.

    Found by running the map against a real repository: both arrived as boxes
    that could never have an edge. Being an adjacency key is the test — the
    graph is Python-only, and every Python module it parsed is a node in it.
    """
    adjacency = _adjacency({"pkg.web": ["pkg.core.run"]}, also=("pkg.core",))
    owners = _owners("pkg.web", "pkg.core", "markdown:README.md:1", "requirements:req.txt:1")

    result = _rollup_modules(adjacency, owners, limit=50)

    assert {m.symbol for m in result.modules} == {"pkg.web", "pkg.core"}
    # And the total reflects what is really on the map, not what was offered.
    assert result.total_modules == 2


def test_a_repo_whose_only_modules_are_non_python_is_unavailable() -> None:
    """Not an empty map — a map that does not apply. Same contract as a repo
    with no graph at all."""
    owners = _owners("markdown:README.md:1")
    assert _rollup_modules({}, owners, limit=50).available is False
