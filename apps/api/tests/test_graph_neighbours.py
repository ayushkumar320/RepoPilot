"""Contract for ``GET /repos/{repo_id}/graph/neighbours``.

The endpoint's job is to say what sits next to a symbol in the indexed
snapshot's code graph, and — where it can — how to open that symbol's source.
The rules it must not break:

* never invent a ``file:line``. A neighbour with no chunk row gets
  ``resolved: false`` and a null ``chunk_id``, not a guessed span.
* ``available: false`` when the snapshot has no graph at all. That is the
  normal case for a repo with no Python, and it has to read as
  not-applicable rather than as an empty, broken diagram.
* ``external`` and ``resolved`` are independent. A symbol can belong to the
  repo and still have no chunk (a nested def the chunker skipped).
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# pytest resolves sibling test modules via rootdir; mypy does not.
from test_api_contract import (  # type: ignore[import-not-found]
    FakeChunkService,
    FakeQAService,
    FakeRepoService,
)

from repopilot_agents.types import CodeRef
from repopilot_api.app import create_app
from repopilot_api.models import GraphModulesResponse, GraphNeighbour, GraphNeighboursResponse
from repopilot_api.services import AppServices, LiveGraphService


class FakeGraphService:
    def __init__(self, response: GraphNeighboursResponse | None = None) -> None:
        self.response = response
        self.calls: list[tuple[str, str, int]] = []

    async def modules(self, repo_id: str, *, limit: int = 60) -> GraphModulesResponse:
        """Present so this fake still satisfies ``GraphService``. The module
        map has its own tests; these are about the neighbourhood read."""
        if repo_id == "unknown-repo":
            raise KeyError(repo_id)
        return GraphModulesResponse(available=False)

    async def neighbours(
        self, repo_id: str, symbol: str, *, limit: int = 60
    ) -> GraphNeighboursResponse:
        self.calls.append((repo_id, symbol, limit))
        if repo_id == "unknown-repo":
            raise KeyError(repo_id)
        if self.response is not None:
            return self.response
        return GraphNeighboursResponse(
            symbol=symbol,
            available=True,
            found=True,
            total=2,
            neighbours=[
                GraphNeighbour(
                    symbol="pkg.mod.helper",
                    label="helper",
                    edge="calls",
                    kind="function",
                    external=False,
                    resolved=True,
                    chunk_id="chunk-abc",
                    ref=CodeRef(
                        file_path="pkg/mod.py", start_line=10, end_line=20, symbol="pkg.mod.helper"
                    ),
                ),
                GraphNeighbour(
                    symbol="json.dumps",
                    label="dumps",
                    edge="imports",
                    external=True,
                    resolved=False,
                ),
            ],
        )


def _services(graph: FakeGraphService | None) -> AppServices:
    repos = FakeRepoService()
    return AppServices(
        repos=repos,
        qa=FakeQAService(repos),
        chunks=FakeChunkService(),
        graph=graph,
    )


async def _client(services: AppServices) -> AsyncClient:
    app: FastAPI = create_app(services=services)
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


@pytest.fixture
async def graph_client() -> AsyncIterator[tuple[AsyncClient, FakeGraphService]]:
    graph = FakeGraphService()
    client = await _client(_services(graph))
    async with client:
        yield client, graph


@pytest.mark.asyncio
async def test_returns_neighbours_with_source_refs(
    graph_client: tuple[AsyncClient, FakeGraphService],
) -> None:
    client, _graph = graph_client
    response = await client.get(
        "/repos/pallets%2Fflask/graph/neighbours", params={"symbol": "pkg.mod.run"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert body["found"] is True
    first = body["neighbours"][0]
    assert first["symbol"] == "pkg.mod.helper"
    assert first["label"] == "helper"
    assert first["edge"] == "calls"
    assert first["chunk_id"] == "chunk-abc"
    assert first["ref"]["file_path"] == "pkg/mod.py"


@pytest.mark.asyncio
async def test_unresolved_neighbour_carries_no_invented_ref(
    graph_client: tuple[AsyncClient, FakeGraphService],
) -> None:
    """A symbol with no chunk row must not be given a fabricated file:line."""
    client, _graph = graph_client
    response = await client.get(
        "/repos/pallets%2Fflask/graph/neighbours", params={"symbol": "pkg.mod.run"}
    )

    external = response.json()["neighbours"][1]
    assert external["resolved"] is False
    assert external["chunk_id"] is None
    assert external["ref"] is None
    assert external["external"] is True


@pytest.mark.asyncio
async def test_symbol_and_limit_reach_the_service() -> None:
    graph = FakeGraphService()
    async with await _client(_services(graph)) as client:
        await client.get(
            "/repos/pallets%2Fflask/graph/neighbours",
            params={"symbol": "pkg.mod.run", "limit": 5},
        )
    # FastAPI's {repo_id:path} converter decodes %2F, so the service sees the
    # decoded display id. That is what the other routes pass too, and
    # normalize_repo_id accepts either form.
    assert graph.calls == [("pallets/flask", "pkg.mod.run", 5)]


@pytest.mark.asyncio
async def test_repo_without_a_graph_reports_unavailable() -> None:
    """No Python in the repo means no graph — say so rather than showing empty."""
    graph = FakeGraphService(
        GraphNeighboursResponse(symbol="whatever", available=False, found=False)
    )
    async with await _client(_services(graph)) as client:
        response = await client.get(
            "/repos/some%2Fjs-repo/graph/neighbours", params={"symbol": "whatever"}
        )

    assert response.status_code == 200
    assert response.json()["available"] is False
    assert response.json()["neighbours"] == []


@pytest.mark.asyncio
async def test_unknown_symbol_is_found_false_not_an_error() -> None:
    graph = FakeGraphService(GraphNeighboursResponse(symbol="nope", available=True, found=False))
    async with await _client(_services(graph)) as client:
        response = await client.get(
            "/repos/pallets%2Fflask/graph/neighbours", params={"symbol": "nope"}
        )

    assert response.status_code == 200
    assert response.json() == {
        "symbol": "nope",
        "available": True,
        "found": False,
        "neighbours": [],
        "total": 0,
        "truncated": False,
    }


@pytest.mark.asyncio
async def test_unknown_repo_is_404() -> None:
    async with await _client(_services(FakeGraphService())) as client:
        response = await client.get("/repos/unknown-repo/graph/neighbours", params={"symbol": "x"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_route_is_404_when_no_graph_service_configured() -> None:
    async with await _client(_services(None)) as client:
        response = await client.get(
            "/repos/pallets%2Fflask/graph/neighbours", params={"symbol": "x"}
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_symbol_is_required() -> None:
    async with await _client(_services(FakeGraphService())) as client:
        response = await client.get("/repos/pallets%2Fflask/graph/neighbours")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_limit_is_capped_by_the_route() -> None:
    async with await _client(_services(FakeGraphService())) as client:
        response = await client.get(
            "/repos/pallets%2Fflask/graph/neighbours",
            params={"symbol": "x", "limit": 10_000},
        )
    assert response.status_code == 422


# ── pure mapping logic ──────────────────────────────────────────────────────


def test_internal_but_unchunked_symbol_is_not_marked_external() -> None:
    """The honesty rule: 'no source found' is not the same as 'third party'."""
    neighbour = LiveGraphService._to_neighbour(
        "pkg.mod.outer.inner",
        "calls",
        {},  # nothing resolved — the chunker never chunked this nested def
        {"pkg"},
        "pkg@sha",
    )
    assert neighbour.external is False
    assert neighbour.resolved is False
    assert neighbour.chunk_id is None
    assert neighbour.ref is None


def test_symbol_outside_the_repo_roots_is_external() -> None:
    neighbour = LiveGraphService._to_neighbour("json.dumps", "imports", {}, {"pkg"}, "pkg@sha")
    assert neighbour.external is True
    assert neighbour.label == "dumps"


def test_resolved_symbol_gets_a_chunk_id_and_ref() -> None:
    neighbour = LiveGraphService._to_neighbour(
        "pkg.mod.helper",
        "called_by",
        {"pkg.mod.helper": ("pkg/mod.py", 10, 20, "function")},
        {"pkg"},
        "pkg@sha",
    )
    assert neighbour.resolved is True
    assert neighbour.kind == "function"
    assert neighbour.chunk_id
    assert neighbour.ref is not None
    assert neighbour.ref.file_path == "pkg/mod.py"
    assert (neighbour.ref.start_line, neighbour.ref.end_line) == (10, 20)
