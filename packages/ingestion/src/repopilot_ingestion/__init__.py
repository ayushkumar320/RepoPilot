"""Phase 1 — clone -> parse -> chunk -> graph -> embed -> persist."""

from repopilot_ingestion.chunk import Chunk, chunk_file
from repopilot_ingestion.clone import (
    CloneResult,
    clone_to_tempdir,
    parse_github_url,
    remote_head_sha,
)
from repopilot_ingestion.graph import ModuleSource, build_graph, graph_to_adjacency
from repopilot_ingestion.parse import ImportEdge, ParsedFile, ParsedSymbol, parse_file
from repopilot_ingestion.pipeline import (
    PipelineResult,
    PipelineStatus,
    index_repo,
    revisit_status,
)

__all__ = [
    "Chunk",
    "CloneResult",
    "ImportEdge",
    "ModuleSource",
    "ParsedFile",
    "ParsedSymbol",
    "PipelineResult",
    "PipelineStatus",
    "build_graph",
    "chunk_file",
    "clone_to_tempdir",
    "graph_to_adjacency",
    "index_repo",
    "parse_file",
    "parse_github_url",
    "remote_head_sha",
    "revisit_status",
]
