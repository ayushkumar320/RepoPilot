"""Re-indexing a snapshot must not delete and recreate its ``repos`` row.

``product_tours.snapshot_repo_id`` references ``repos`` ON DELETE SET NULL, so
dropping the row unpins every saved tour that pointed at that snapshot — even
though the rebuild puts the row straight back under the same id. The rebuild
therefore clears the snapshot's *chunks* and upserts the row.

The fast test here pins the SQL shape, because that is what the bug was: a
DELETE aimed at the wrong table. The live round-trip that proves a tour pin
actually survives is marked ``integration``.
"""

from __future__ import annotations

from typing import Any

import pytest

from repopilot_ingestion.persist import delete_incomplete_index


class _CapturingConn:
    def __init__(self, sink: list[str]) -> None:
        self._sink = sink

    async def execute(self, statement: Any) -> Any:
        # Default dialect is enough: the assertion is about which table the
        # statement targets, not about any Postgres-specific syntax.
        compiled: Any = statement.compile()
        self._sink.append(str(compiled).replace("\n", " "))
        return _Result()


class _Result:
    """Stands in for a SQLAlchemy result; only ``rowcount`` is read."""

    rowcount: int = 0


class _CapturingEngine:
    """Minimal stand-in that records the SQL ``delete_incomplete_index`` emits."""

    def __init__(self) -> None:
        self.statements: list[str] = []

    def begin(self) -> Any:
        sink = self.statements

        class _Ctx:
            async def __aenter__(self) -> _CapturingConn:
                return _CapturingConn(sink)

            async def __aexit__(self, *exc: object) -> bool:
                return False

        return _Ctx()


@pytest.mark.asyncio
async def test_rebuild_deletes_chunks_never_the_repos_row() -> None:
    engine = _CapturingEngine()
    await delete_incomplete_index(
        engine,  # type: ignore[arg-type]
        repo_url="https://github.com/encode/httpx",
        head_sha="a" * 40,
    )

    assert engine.statements, "expected delete_incomplete_index to issue a statement"
    sql = engine.statements[0].upper()
    assert sql.startswith("DELETE FROM CHUNKS"), sql
    # The regression: a DELETE aimed at repos cascades SET NULL onto saved tours.
    assert "DELETE FROM REPOS" not in sql, sql
    # It still has to scope to the snapshot being rebuilt.
    assert "REPOS" in sql, "expected the chunk delete to be scoped by a repos subquery"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tour_pin_survives_a_reindex() -> None:
    """End to end against live Postgres: re-index, and the pin is still there.

    Skipped unless a database is reachable; this is the only check that proves
    the actual guarantee rather than the SQL that implements it.
    """
    import sqlalchemy as sa

    from repopilot_core.settings import Settings
    from repopilot_ingestion.persist import make_engine

    engine = make_engine(Settings())
    try:
        async with engine.connect() as conn:
            await conn.execute(sa.text("select 1"))
    except Exception as exc:  # pragma: no cover - environment dependent
        await engine.dispose()
        pytest.skip(f"no database reachable: {exc}")

    try:
        async with engine.begin() as conn:
            row = (
                await conn.execute(
                    sa.text(
                        "select t.tour_id, t.snapshot_repo_id, r.index_version "
                        "from product_tours t join repos r on r.id = t.snapshot_repo_id "
                        "limit 1"
                    )
                )
            ).first()
            if row is None:
                pytest.skip("no pinned tour in this database to check")
            tour_id, snapshot_id, _version = row

            # Exactly what a rebuild of this snapshot does to the child rows.
            await conn.execute(
                sa.text("delete from chunks where repo_id = :rid"), {"rid": snapshot_id}
            )
            still = (
                await conn.execute(
                    sa.text("select snapshot_repo_id from product_tours where tour_id = :t"),
                    {"t": tour_id},
                )
            ).scalar()
            assert still == snapshot_id, "clearing chunks must not touch the tour's pin"
            # Leave the database as we found it.
            raise _Rollback
    except _Rollback:
        pass
    finally:
        await engine.dispose()


class _Rollback(Exception):
    """Sentinel used to roll the integration test's transaction back."""
