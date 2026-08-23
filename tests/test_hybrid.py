import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.retrieval.hybrid import hybrid_search, reciprocal_rank_fusion


def test_rrf_boosts_items_appearing_in_both_lists():
    dense = ["a", "b", "c"]
    sparse = ["x", "b", "y"]
    scores = reciprocal_rank_fusion([dense, sparse], k=60)
    # 'b' hem dense'te 2. hem sparse'ta 2. sırada -> en yüksek skor onda olmalı
    assert scores["b"] > scores["a"]
    assert scores["b"] > scores["x"]


def test_rrf_item_only_in_one_list_still_scored():
    dense = ["a", "b"]
    sparse = []
    scores = reciprocal_rank_fusion([dense, sparse], k=60)
    assert "a" in scores
    assert scores["a"] > scores["b"]  # 'a' daha üst sırada


def test_rrf_higher_rank_scores_higher():
    dense = ["a", "b", "c", "d"]
    scores = reciprocal_rank_fusion([dense], k=60)
    assert scores["a"] > scores["b"] > scores["c"] > scores["d"]


class FakeEmbedder:
    def embed_query(self, text):
        return [1.0, 0.0]


class FakeVectorStore:
    def __init__(self, ordered_results):
        self._ordered = ordered_results

    def query(self, query_embedding, n_results=5, where=None):
        return self._ordered[:n_results]

    def count(self):
        return len(self._ordered)


class FakeBM25Index:
    def __init__(self, ordered_results):
        self._ordered = ordered_results

    def search(self, query, top_k=5):
        return self._ordered[:top_k]


def _make_chunk_result(chunk_id, text="metin", **meta):
    return {
        "chunk_id": chunk_id,
        "text": text,
        "metadata": {
            "doc_id": "doc1",
            "madde_no": "1",
            "fikra_no": None,
            "bent_no": None,
            "madde_baslik": None,
            "bolum": None,
            "section": None,
            **meta,
        },
    }


def test_hybrid_search_marks_items_found_in_both():
    dense = [_make_chunk_result("c1"), _make_chunk_result("c2")]
    sparse = [
        {"chunk_id": "c1", "text": "metin", "doc_id": "doc1", "madde_no": "1"},
        {"chunk_id": "c3", "text": "metin", "doc_id": "doc1", "madde_no": "1"},
    ]

    results = hybrid_search(
        "sorgu",
        FakeEmbedder(),
        FakeVectorStore(dense),
        FakeBM25Index(sparse),
        top_k=5,
    )

    by_id = {r["chunk_id"]: r for r in results}
    assert by_id["c1"]["in_dense"] is True
    assert by_id["c1"]["in_sparse"] is True
    assert by_id["c2"]["in_dense"] is True
    assert by_id["c2"]["in_sparse"] is False
    assert by_id["c3"]["in_sparse"] is True
    assert by_id["c3"]["in_dense"] is False
    # 'c1' her iki listede de olduğu için en yüksek RRF skoruna sahip olmalı
    assert by_id["c1"]["rrf_score"] == max(r["rrf_score"] for r in results)
