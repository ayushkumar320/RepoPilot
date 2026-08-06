"""``bm25_search`` — Postgres full-text (BM25-style) keyword search.

The sparse half of hybrid retrieval. Where ``vector_search`` embeds the query
and ranks by cosine distance, ``bm25_search`` ranks by ``ts_rank_cd`` over the
``chunks.content_tsv`` GIN index (added in migration 0002). It exists to catch
what dense embeddings miss: **rare exact tokens** — symbol names, error
strings, decorator names, config keys — which the embedder has never seen and
smears across unrelated neighbours.

Matches the ``simple`` analyzer used to build ``content_tsv`` (no stemming,
preserves code identifiers). Returns ``ChunkHit`` with ``distance = 1 -
normalized_score`` so it composes with the dense lane under RRF.

``WHERE repo_id = ...`` is non-negotiable — we never mix corpora across repos.
The metadata filters mirror ``vector_search`` so a future query-understanding
step can drive both lanes with the same hints.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from repopilot_agents.types import ChunkHit, CodeRef

log = structlog.get_logger(__name__)

# The content_tsv column uses the 'simple' analyzer (identifier-preserving, no
# stemming) but that also means NO stopword removal. With OR-semantics that
# lets question words ("how", "where", "the") match huge swaths of the corpus
# and dilute ts_rank_cd, drowning the rare high-signal token. So we strip a
# compact English stopword set at query time — the sparse lane then keys on
# content words + identifiers only. Kept deliberately small: only true noise
# words, never anything that could be a code token.
_STOPWORDS = frozenset(
    [
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "does",
        "do",
        "for",
        "from",
        "how",
        "in",
        "into",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "with",
        "would",
        "could",
        "should",
        "will",
        "can",
    ]
)


def clean_query(query: str) -> str:
    """Drop stopwords, keeping content words and identifiers for the sparse lane."""
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", query)
    kept = [t for t in tokens if t.lower() not in _STOPWORDS]
    return " ".join(kept)


# OR-semantics tsquery. plainto_tsquery ANDs its terms, which is fatal for
# code search: a verbose natural-language question ("where is the GZipDecoder
# defined?") would require the chunk to contain "where"/"is"/"the" too, and
# code chunks don't — so @@ matches nothing. We rewrite '&' to '|' so any term
# can match, and let ts_rank_cd rank by weighted term density (the rare,
# high-signal token dominates). 'simple' matches the analyzer content_tsv was
# built with (migration 0002) — the configs MUST agree or lexemes won't line up.
_TSQUERY = "replace(plainto_tsquery('simple', :q)::text, '&', '|')::tsquery"
# ts_rank_cd weight array is {D, C, B, A}. The symbol is indexed in band A
# (migration 0002), so weighting A=1.0 and body D=0.1 makes a chunk whose
# *symbol* matches the query dominate one that only mentions the term in its
# body — the IDF substitute for rare-symbol retrieval. Band B (migration 0009)
# holds the symbol split on case and ``._`` boundaries, so prose ("transport
# handle request") reaches ``HTTPTransport.handle_request``; at 0.4 it ranks
# below an exact symbol hit and above a body mention.
_RANK_WEIGHTS = "'{0.1, 0.2, 0.4, 1.0}'"


def build_bm25_sql(
    *,
    kind: str | None,
    path_prefix: str | None,
    exclude_path_prefixes: Sequence[str],
) -> str:
    """Compose the FTS query with optional metadata filters (pure)."""
    clauses = [
        "c.repo_id = :repo_id",
        f"c.content_tsv @@ {_TSQUERY}",
    ]
    if kind is not None:
        clauses.append("c.kind = :kind")
    if path_prefix is not None:
        clauses.append("c.file_path LIKE :path_prefix || '%'")
    for i in range(len(exclude_path_prefixes)):
        clauses.append(f"c.file_path NOT LIKE :exclude_{i} || '%'")
    where = "\n          AND ".join(clauses)
    return f"""
        SELECT c.file_path, c.start_line, c.end_line, c.symbol, c.kind, c.summary,
               ts_rank_cd({_RANK_WEIGHTS}, c.content_tsv, {_TSQUERY}) AS score
        FROM chunks c
        WHERE {where}
        ORDER BY score DESC
        LIMIT :k
        """


async def bm25_search(
    query: str,
    *,
    engine: AsyncEngine,
    repo_id: str,
    k: int = 50,
    kind: str | None = None,
    path_prefix: str | None = None,
    exclude_path_prefixes: Sequence[str] = (),
) -> list[ChunkHit]:
    """Return up to ``k`` keyword-matched chunks for ``query`` in ``repo_id``.

    Empty for a blank query or one that tokenizes to nothing (all stopwords /
    punctuation) — ``plainto_tsquery`` yields an empty query that ``@@``
    matches nothing, which is the correct honest-empty behaviour for the
    not-in-repo / nonsense-token case.
    """
    cleaned = clean_query(query)
    if not cleaned or k <= 0:
        return []

    sql = text(
        build_bm25_sql(
            kind=kind,
            path_prefix=path_prefix,
            exclude_path_prefixes=exclude_path_prefixes,
        )
    )
    params: dict[str, object] = {"q": cleaned, "repo_id": repo_id, "k": k}
    if kind is not None:
        params["kind"] = kind
    if path_prefix is not None:
        params["path_prefix"] = path_prefix
    for i, prefix in enumerate(exclude_path_prefixes):
        params[f"exclude_{i}"] = prefix

    async with engine.connect() as conn:
        rows = (await conn.execute(sql, params)).all()

    # Normalize ts_rank_cd (unbounded, but monotone) to a [0,1)-ish distance by
    # rank within this result set — RRF only uses order, so exact values are
    # cosmetic; we keep distance monotone with relevance for any consumer that
    # reads it directly.
    hits: list[ChunkHit] = []
    top = float(rows[0][6]) if rows else 0.0
    for file_path, start_line, end_line, symbol, kind_, summary, score in rows:
        norm = float(score) / top if top > 0 else 0.0
        hits.append(
            ChunkHit(
                ref=CodeRef(
                    file_path=file_path,
                    start_line=int(start_line),
                    end_line=int(end_line),
                    symbol=symbol,
                ),
                distance=max(0.0, 1.0 - norm),
                summary=summary,
                kind=kind_,
            )
        )
    log.debug("bm25_search.done", repo_id=repo_id, k=k, hits=len(hits))
    return hits


__all__ = ["bm25_search", "build_bm25_sql"]
