"""Module naming and relative-import resolution in the graph builder.

Two defects made the code graph a poor map of the repo's own architecture, and
both were invisible in review because the graph still built and still rendered:

* ``_path_to_module`` named modules from the repo-relative path, so in a
  src-layout repo ``src/pkg/mod.py`` was defined as ``src.pkg.mod`` while every
  import of it said ``pkg.mod``. Defining node and imported node were different
  strings, so no internal edge ever joined them.
* ``visit_ImportFrom`` returned early on every relative import, which also
  starved the alias map that resolves cross-module calls.

Measured on RepoPilot's own packages/ before the fix: 0 cross-module edges and
20 phantom twin nodes. After: 342 and 1.
"""

from __future__ import annotations

from pathlib import Path

import networkx as nx

from repopilot_ingestion.graph import ModuleSource, build_graph
from repopilot_ingestion.pipeline import _path_to_module


def _mk(root: Path, rel: str, body: str = "") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


# ── module naming ───────────────────────────────────────────────────────────


def test_src_layout_module_name_starts_at_the_package_root(tmp_path: Path) -> None:
    """The name must match what the code's own imports say, not the path."""
    _mk(tmp_path, "src/pkg/__init__.py")
    _mk(tmp_path, "src/pkg/mod.py")
    assert _path_to_module(Path("src/pkg/mod.py"), root=tmp_path) == "pkg.mod"


def test_nested_packages_keep_every_packaged_level(tmp_path: Path) -> None:
    _mk(tmp_path, "packages/a/src/pkg/__init__.py")
    _mk(tmp_path, "packages/a/src/pkg/sub/__init__.py")
    _mk(tmp_path, "packages/a/src/pkg/sub/mod.py")
    rel = Path("packages/a/src/pkg/sub/mod.py")
    assert _path_to_module(rel, root=tmp_path) == "pkg.sub.mod"


def test_package_init_names_the_package_itself(tmp_path: Path) -> None:
    _mk(tmp_path, "src/pkg/__init__.py")
    assert _path_to_module(Path("src/pkg/__init__.py"), root=tmp_path) == "pkg"


def test_flat_layout_is_unchanged(tmp_path: Path) -> None:
    """Repos that were already correct must not move."""
    _mk(tmp_path, "pkg/__init__.py")
    _mk(tmp_path, "pkg/mod.py")
    assert _path_to_module(Path("pkg/mod.py"), root=tmp_path) == "pkg.mod"


def test_file_outside_any_package_is_its_basename(tmp_path: Path) -> None:
    """No __init__.py anywhere, so Python would import it as the bare name."""
    _mk(tmp_path, "scripts/tool.py")
    assert _path_to_module(Path("scripts/tool.py"), root=tmp_path) == "tool"
    _mk(tmp_path, "setup.py")
    assert _path_to_module(Path("setup.py"), root=tmp_path) == "setup"


def test_without_root_falls_back_to_the_relative_path(tmp_path: Path) -> None:
    """Callers with no clone on disk keep the old behaviour rather than break."""
    assert _path_to_module(Path("src/pkg/mod.py")) == "src.pkg.mod"


# ── relative imports ────────────────────────────────────────────────────────


def _graph_for(files: dict[str, tuple[str, str]]) -> nx.DiGraph[str]:
    """Build a graph from ``{module: (rel_path, source)}``.

    ``rel_path`` matters: it is how the builder tells a package's ``__init__.py``
    from a plain module, which decides what a relative import counts levels from.
    """
    mods = [
        ModuleSource(module=module, rel_path=rel, source=src)
        for module, (rel, src) in files.items()
    ]
    return build_graph(mods)


def test_relative_import_resolves_to_the_owning_package() -> None:
    """``from . import helper`` inside pkg.mod must point at pkg.helper."""
    graph = _graph_for(
        {
            "pkg": ("pkg/__init__.py", ""),
            "pkg.helper": ("pkg/helper.py", "def assist():\n    return 1\n"),
            "pkg.mod": ("pkg/mod.py", "from . import helper\n"),
        }
    )
    assert graph.has_edge("pkg.mod", "pkg.helper")


def test_relative_from_submodule_resolves() -> None:
    """``from .helper import assist`` -> pkg.helper.assist."""
    graph = _graph_for(
        {
            "pkg": ("pkg/__init__.py", ""),
            "pkg.helper": ("pkg/helper.py", "def assist():\n    return 1\n"),
            "pkg.mod": ("pkg/mod.py", "from .helper import assist\n"),
        }
    )
    assert graph.has_edge("pkg.mod", "pkg.helper.assist")


def test_parent_relative_import_climbs_one_level() -> None:
    """``from .. import sibling`` inside pkg.sub.mod -> pkg.sibling."""
    graph = _graph_for(
        {
            "pkg": ("pkg/__init__.py", ""),
            "pkg.sibling": ("pkg/sibling.py", ""),
            "pkg.sub": ("pkg/sub/__init__.py", ""),
            "pkg.sub.mod": ("pkg/sub/mod.py", "from .. import sibling\n"),
        }
    )
    assert graph.has_edge("pkg.sub.mod", "pkg.sibling")


def test_package_init_relative_import_stays_in_its_own_package() -> None:
    """In pkg/__init__.py the package IS pkg, not pkg's parent."""
    graph = _graph_for(
        {
            "pkg": ("pkg/__init__.py", "from .core import Thing\n"),
            "pkg.core": ("pkg/core.py", "class Thing:\n    pass\n"),
        }
    )
    assert graph.has_edge("pkg", "pkg.core.Thing")


def test_relative_import_above_the_root_is_dropped_not_invented() -> None:
    """Climbing past the top package has no answer, so emit no edge."""
    graph = _graph_for({"mod": ("mod.py", "from .. import mystery\n")})
    assert not any(dst.endswith("mystery") for _, dst in graph.edges())


def test_relative_import_feeds_the_alias_map_for_calls() -> None:
    """The dropped-import bug also broke call resolution; this is the payoff."""
    graph = _graph_for(
        {
            "pkg": ("pkg/__init__.py", ""),
            "pkg.helper": ("pkg/helper.py", "def assist():\n    return 1\n"),
            "pkg.mod": (
                "pkg/mod.py",
                "from .helper import assist\n\n\ndef run():\n    return assist()\n",
            ),
        }
    )
    assert graph.has_edge("pkg.mod.run", "pkg.helper.assist")
