import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.retrieval.pipeline import DOC_TYPE_BOOST_MULTIPLIER, retrieve


class FakeReranker:
    """Her chunk'a sabit (veya haritalanmis) bir rerank_score atar."""

    def __init__(self, score_by_chunk_id=None, default_score=1.0):
        self.score_by_chunk_id = score_by_chunk_id or {}
        self.default_score = default_score
        self.calls = []

    def rerank_with_safety_net(self, query, candidates, top_k=5, guard_pool=None):
        self.calls.append({"query": query, "n_candidates": len(candidates), "guard_pool": guard_pool})
        scored = [
            {**c, "rerank_score": self.score_by_chunk_id.get(c["chunk_id"], self.default_score)}
            for c in candidates
        ]
        scored.sort(key=lambda c: c["rerank_score"], reverse=True)
        return scored[:top_k]


def _chunk(chunk_id, doc_id="doc1", rrf_score=0.05, madde_kind="MADDE", madde_no="1"):
    return {
        "chunk_id": chunk_id,
        "doc_id": doc_id,
        "rrf_score": rrf_score,
        "madde_kind": madde_kind,
        "madde_no": madde_no,
        "text": "metin",
    }


def test_retrieve_calls_expand_query_and_merges_subquery_results():
    c1 = _chunk("c1")
    c2 = _chunk("c2")
    reranker = FakeReranker()

    def fake_hybrid(query, *args, **kwargs):
        return [c1] if query == "soru" else [c2]

    with patch("src.retrieval.pipeline.hybrid_search", side_effect=fake_hybrid), \
         patch("src.retrieval.pipeline.expand_query", return_value=["soru", "soru adim adim sureci", "soru sureler istisnalar"]) as mock_expand, \
         patch("src.retrieval.pipeline.get_query_type", return_value="genel_hukum") as mock_query_type:
        result = retrieve("soru", embedder=object(), vector_store=object(), bm25_index=object(), reranker=reranker)

    mock_expand.assert_called_once()
    mock_query_type.assert_called_once()
    assert result.query_type == "genel_hukum"
    chunk_ids = {c["chunk_id"] for c in result.chunks}
    assert "c1" in chunk_ids
    assert "c2" in chunk_ids


def test_retrieve_applies_doc_type_boost_for_guncel_deger_queries():
    karar_chunk = _chunk("c1", doc_id="karar-x", rrf_score=0.02)
    yonetmelik_chunk = _chunk("c2", doc_id="yonetmelik-x", rrf_score=0.021)
    reranker = FakeReranker()

    def fake_hybrid(query, *args, **kwargs):
        return [dict(karar_chunk), dict(yonetmelik_chunk)]

    with patch("src.retrieval.pipeline.hybrid_search", side_effect=fake_hybrid), \
         patch("src.retrieval.pipeline.expand_query", return_value=["soru"]), \
         patch("src.retrieval.pipeline.get_query_type", return_value="guncel_deger"):
        result = retrieve(
            "soru", embedder=object(), vector_store=object(), bm25_index=object(), reranker=reranker,
            doc_types={"karar-x": "karar", "yonetmelik-x": "yonetmelik"},
        )

    boosted = next(c for c in result.chunks if c["chunk_id"] == "c1")
    assert boosted["rrf_score"] == 0.02 * DOC_TYPE_BOOST_MULTIPLIER
    assert boosted["rrf_score"] > yonetmelik_chunk["rrf_score"]


def test_retrieve_does_not_boost_without_matching_query_type():
    karar_chunk = _chunk("c1", doc_id="karar-x", rrf_score=0.02)
    reranker = FakeReranker()

    with patch("src.retrieval.pipeline.hybrid_search", return_value=[dict(karar_chunk)]), \
         patch("src.retrieval.pipeline.expand_query", return_value=["soru"]), \
         patch("src.retrieval.pipeline.get_query_type", return_value="genel_hukum"):
        result = retrieve(
            "soru", embedder=object(), vector_store=object(), bm25_index=object(), reranker=reranker,
            doc_types={"karar-x": "karar"},
        )

    assert result.chunks[0]["rrf_score"] == 0.02


def test_retrieve_attaches_ek_sibling_chunks():
    # Final (top_k=8) listede bir EK chunk secilip digeri top_k disinda
    # kaldiysa (8 "dolgu" chunk ek::p2'yi disari itiyor), ayni ek'in
    # disarida kalan parcasi yine de sonuca eklenmeli.
    ek1 = _chunk("ek::p1", madde_kind="EK", madde_no="1")
    ek2 = _chunk("ek::p2", madde_kind="EK", madde_no="1")
    fillers = [_chunk(f"filler{i}") for i in range(8)]
    scores = {"ek::p1": 5.0, "ek::p2": -5.0}
    scores.update({f"filler{i}": 1.0 for i in range(8)})
    reranker = FakeReranker(score_by_chunk_id=scores)

    with patch("src.retrieval.pipeline.hybrid_search", return_value=[ek1, ek2] + fillers), \
         patch("src.retrieval.pipeline.expand_query", return_value=["soru"]), \
         patch("src.retrieval.pipeline.get_query_type", return_value="genel_hukum"):
        result = retrieve("soru", embedder=object(), vector_store=object(), bm25_index=object(), reranker=reranker)

    chunk_ids = {c["chunk_id"] for c in result.chunks}
    assert "ek::p1" in chunk_ids
    assert "ek::p2" in chunk_ids
