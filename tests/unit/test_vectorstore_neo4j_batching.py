"""Unit tests for Neo4j vector store query batching.

Tests cover:
- search_with_graph_context issues exactly ONE enrichment query
  regardless of result count (N+1 fix)
- Enrichment results merged per-chunk with identical semantics
- Graceful degradation when the enrichment query fails
- Batch relationship writers (technique / CVE) use a single query
- Singular relationship methods delegate to the batch versions
- get_related_chunks depth validation (Cypher forbids $param in
  variable-length path bounds)

Issue #72: Fix N+1 Query Problem in Graph Enrichment
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from ciicerone.rag.vectorstore import Neo4jStore
from ciicerone.rag.models import Chunk, SearchResult


# ==========================================
# Test helpers
# ==========================================

class FakeNeo4jResult:
    """Mimics the neo4j async Result object."""

    def __init__(self, rows=None):
        self._rows = rows or []

    async def data(self):
        return self._rows

    async def single(self):
        return self._rows[0] if self._rows else None

    async def consume(self):
        return None


def make_store(run_result=None, run_side_effect=None):
    """Build a Neo4jStore with a fully mocked async driver/session."""
    config = Mock()
    config.collection_name = "neo4j"
    store = Neo4jStore(config)

    session = MagicMock()
    session.run = AsyncMock(
        return_value=run_result if run_result is not None else FakeNeo4jResult(),
        side_effect=run_side_effect,
    )

    session_ctx = MagicMock()
    session_ctx.__aenter__ = AsyncMock(return_value=session)
    session_ctx.__aexit__ = AsyncMock(return_value=False)

    driver = MagicMock()
    driver.session = MagicMock(return_value=session_ctx)
    store._driver = driver
    return store, session


def make_search_result(chunk_id: str) -> SearchResult:
    chunk = Chunk(
        id=chunk_id,
        document_id="doc-1",
        content=f"content for {chunk_id}",
        chunk_index=0,
        start_char=0,
        end_char=0,
        metadata={},
    )
    return SearchResult(chunk=chunk, similarity_score=0.9)


def enrichment_row(chunk_id: str):
    return {
        "chunk_id": chunk_id,
        "techniques": [
            {"technique_id": "T1566", "technique_name": "Phishing", "tactic": "Initial Access"}
        ],
        "cves": [
            {"cve_id": "CVE-2024-0001", "severity": "high", "description": "test"}
        ],
        "threat_actors": ["APT99"],
    }


# ==========================================
# search_with_graph_context — N+1 fix
# ==========================================

async def test_enrichment_uses_single_query_for_many_results():
    """The core N+1 fix: 25 results must produce exactly 1 enrichment query."""
    n = 25
    base = [make_search_result(f"chunk-{i}") for i in range(n)]
    rows = [enrichment_row(f"chunk-{i}") for i in range(n)]
    store, session = make_store(run_result=FakeNeo4jResult(rows))

    with patch.object(store, "search", AsyncMock(return_value=base)):
        results = await store.search_with_graph_context([0.1] * 8, top_k=n)

    # Previously: n round-trips. Now: exactly one.
    assert session.run.await_count == 1
    assert len(results) == n

    # The single query must carry every chunk id.
    _, kwargs = session.run.await_args
    assert sorted(kwargs["chunk_ids"]) == sorted(f"chunk-{i}" for i in range(n))


async def test_enrichment_merges_metadata_per_chunk():
    base = [make_search_result("chunk-a"), make_search_result("chunk-b")]
    rows = [enrichment_row("chunk-a")]  # only chunk-a has graph context
    store, _ = make_store(run_result=FakeNeo4jResult(rows))

    with patch.object(store, "search", AsyncMock(return_value=base)):
        results = await store.search_with_graph_context([0.1] * 8, top_k=2)

    enriched = {r.chunk.id: r.chunk.metadata for r in results}
    assert enriched["chunk-a"]["techniques"][0]["technique_id"] == "T1566"
    assert enriched["chunk-a"]["cves"][0]["cve_id"] == "CVE-2024-0001"
    assert enriched["chunk-a"]["threat_actors"] == ["APT99"]
    # chunk-b had no enrichment row — metadata untouched
    assert "techniques" not in enriched["chunk-b"]


async def test_enrichment_skipped_when_no_results():
    store, session = make_store()

    with patch.object(store, "search", AsyncMock(return_value=[])):
        results = await store.search_with_graph_context([0.1] * 8, top_k=10)

    assert results == []
    session.run.assert_not_awaited()


async def test_enrichment_skipped_when_expansion_disabled():
    base = [make_search_result("chunk-a")]
    store, session = make_store()

    with patch.object(store, "search", AsyncMock(return_value=base)):
        results = await store.search_with_graph_context(
            [0.1] * 8, top_k=1, expand_techniques=False, expand_cves=False
        )

    assert results == base
    session.run.assert_not_awaited()


async def test_enrichment_failure_returns_base_results():
    """Enrichment is best-effort — a query failure must not lose results."""
    base = [make_search_result("chunk-a"), make_search_result("chunk-b")]
    store, _ = make_store(run_side_effect=RuntimeError("neo4j down"))

    with patch.object(store, "search", AsyncMock(return_value=base)):
        results = await store.search_with_graph_context([0.1] * 8, top_k=2)

    assert results == base
    assert "techniques" not in results[0].chunk.metadata


# ==========================================
# Batch relationship writers
# ==========================================

async def test_add_technique_relationships_single_query():
    store, session = make_store()
    rels = [
        {"chunk_id": f"chunk-{i}", "technique_id": f"T{1000 + i}"} for i in range(50)
    ]

    await store.add_technique_relationships(rels)

    assert session.run.await_count == 1
    _, kwargs = session.run.await_args
    assert kwargs["rels"] == rels


async def test_add_technique_relationships_empty_is_noop():
    store, session = make_store()
    await store.add_technique_relationships([])
    session.run.assert_not_awaited()


async def test_add_technique_relationship_delegates_to_batch():
    store, session = make_store()

    await store.add_technique_relationship("chunk-a", "T1566")

    assert session.run.await_count == 1
    _, kwargs = session.run.await_args
    assert kwargs["rels"] == [{"chunk_id": "chunk-a", "technique_id": "T1566"}]


async def test_add_cve_relationships_single_query():
    store, session = make_store()
    rels = [
        {"chunk_id": f"chunk-{i}", "cve_id": f"CVE-2024-{i:04d}", "severity": "high"}
        for i in range(50)
    ]

    await store.add_cve_relationships(rels)

    assert session.run.await_count == 1
    _, kwargs = session.run.await_args
    assert kwargs["rels"] == rels


async def test_add_cve_relationship_delegates_to_batch():
    store, session = make_store()

    await store.add_cve_relationship("chunk-a", "CVE-2024-0001", severity="critical")

    assert session.run.await_count == 1
    _, kwargs = session.run.await_args
    assert kwargs["rels"] == [
        {"chunk_id": "chunk-a", "cve_id": "CVE-2024-0001", "severity": "critical"}
    ]


# ==========================================
# get_related_chunks — depth handling
# ==========================================

async def test_get_related_chunks_interpolates_depth():
    store, session = make_store(run_result=FakeNeo4jResult([]))

    await store.get_related_chunks("chunk-a", depth=3)

    args, kwargs = session.run.await_args
    query = args[0]
    assert "[*1..3]" in query
    assert "$depth" not in query
    assert kwargs == {"chunk_id": "chunk-a"}


async def test_get_related_chunks_clamps_depth():
    store, session = make_store(run_result=FakeNeo4jResult([]))

    await store.get_related_chunks("chunk-a", depth=99)
    assert "[*1..5]" in session.run.await_args[0][0]

    await store.get_related_chunks("chunk-a", depth=0)
    assert "[*1..1]" in session.run.await_args[0][0]
