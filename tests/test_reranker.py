import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.retrieval.reranker import Reranker


class FakeCrossEncoder:
    """Gerçek model indirmeden test etmek için: metin uzunluğuna göre
    deterministik bir "alaka skoru" üretir (sadece test amaçlı)."""

    def __init__(self, score_map: dict[str, float]):
        self.score_map = score_map
        self.last_pairs = None

    def predict(self, pairs):
        self.last_pairs = pairs
        return [self.score_map.get(text, 0.0) for _, text in pairs]


def test_rerank_reorders_by_score():
    candidates = [
        {"chunk_id": "c1", "text": "az alakalı metin"},
        {"chunk_id": "c2", "text": "çok alakalı metin"},
        {"chunk_id": "c3", "text": "orta alakalı metin"},
    ]
    fake = FakeCrossEncoder(
        {"az alakalı metin": 0.1, "çok alakalı metin": 0.9, "orta alakalı metin": 0.5}
    )
    reranker = Reranker(model=fake)

    results = reranker.rerank("sorgu", candidates, top_k=3)

    assert [r["chunk_id"] for r in results] == ["c2", "c3", "c1"]


def test_rerank_respects_top_k():
    candidates = [{"chunk_id": f"c{i}", "text": f"metin {i}"} for i in range(10)]
    fake = FakeCrossEncoder({f"metin {i}": float(i) for i in range(10)})
    reranker = Reranker(model=fake)

    results = reranker.rerank("sorgu", candidates, top_k=3)

    assert len(results) == 3
    assert results[0]["chunk_id"] == "c9"  # en yüksek skor


def test_rerank_sends_query_paired_with_each_text():
    candidates = [{"chunk_id": "c1", "text": "metin bir"}]
    fake = FakeCrossEncoder({"metin bir": 1.0})
    reranker = Reranker(model=fake)

    reranker.rerank("test sorgusu", candidates, top_k=1)

    assert fake.last_pairs == [("test sorgusu", "metin bir")]


def test_rerank_empty_candidates_returns_empty():
    fake = FakeCrossEncoder({})
    reranker = Reranker(model=fake)
    assert reranker.rerank("sorgu", [], top_k=5) == []


def test_rerank_adds_score_field_without_losing_original_data():
    candidates = [{"chunk_id": "c1", "text": "metin", "doc_id": "d1", "madde_no": "5"}]
    fake = FakeCrossEncoder({"metin": 0.7})
    reranker = Reranker(model=fake)

    results = reranker.rerank("sorgu", candidates, top_k=1)

    assert results[0]["doc_id"] == "d1"
    assert results[0]["madde_no"] == "5"
    assert results[0]["rerank_score"] == 0.7


def test_safety_net_rescues_top_hybrid_result_when_dropped():
    """Gerçek bir vakadan: hybrid'in en güçlü sonucu, reranker tarafından
    tamamen gözden kaçırılabiliyor. Güvenlik ağı onu geri getirmeli."""
    candidates = [
        {"chunk_id": "hybrid_top", "text": "hybrid'in en güçlü bulduğu doğru sonuç"},
        {"chunk_id": "c2", "text": "ikinci aday"},
        {"chunk_id": "c3", "text": "üçüncü aday"},
    ]
    # Reranker bilerek hybrid_top'u düşük, diğerlerini yüksek puanlıyor.
    fake = FakeCrossEncoder(
        {
            "hybrid'in en güçlü bulduğu doğru sonuç": -5.0,
            "ikinci aday": 3.0,
            "üçüncü aday": 2.0,
        }
    )
    reranker = Reranker(model=fake)

    # top_k=2 olduğu için normal rerank() hybrid_top'u kesinlikle eler.
    normal_result = reranker.rerank("sorgu", candidates, top_k=2)
    assert "hybrid_top" not in [r["chunk_id"] for r in normal_result]

    rescued_result = reranker.rerank_with_safety_net("sorgu", candidates, top_k=2)
    rescued_ids = [r["chunk_id"] for r in rescued_result]
    assert "hybrid_top" in rescued_ids
    assert len(rescued_result) == 2


def test_safety_net_rescues_rank_three_hybrid_result_too():
    """
    Gerçek bir vakadan (eval iyileştirme turu): doğru cevap hybrid'in
    1. değil 3. sırasındaydı, ve 1. sıra reranker sonrası hayatta kaldığı
    için eski (guard_top_n=1) güvenlik ağı hiç devreye girmiyordu. Yeni
    güvenlik ağı ilk 3'ü de korumalı.
    """
    candidates = [
        {"chunk_id": "rank1", "text": "hybrid 1. sıra, alakalı ama tam doğru değil"},
        {"chunk_id": "rank2", "text": "hybrid 2. sıra, alakasız"},
        {"chunk_id": "rank3_correct", "text": "hybrid 3. sıra, asıl doğru cevap"},
        {"chunk_id": "rank4", "text": "hybrid 4. sıra"},
    ]
    # Reranker rank1'i hayatta bırakıyor ama rank3_correct'i tamamen eliyor.
    fake = FakeCrossEncoder(
        {
            "hybrid 1. sıra, alakalı ama tam doğru değil": 1.0,
            "hybrid 2. sıra, alakasız": 5.0,
            "hybrid 3. sıra, asıl doğru cevap": -10.0,
            "hybrid 4. sıra": 4.0,
        }
    )
    reranker = Reranker(model=fake)

    normal_result = reranker.rerank("sorgu", candidates, top_k=3)
    assert "rank3_correct" not in [r["chunk_id"] for r in normal_result]

    rescued_result = reranker.rerank_with_safety_net("sorgu", candidates, top_k=3, guard_top_n=3)
    assert "rank3_correct" in [r["chunk_id"] for r in rescued_result]
    assert len(rescued_result) == 3


def test_safety_net_does_nothing_when_top_hybrid_already_survives():
    candidates = [
        {"chunk_id": "c1", "text": "en iyi sonuç"},
        {"chunk_id": "c2", "text": "ikinci"},
    ]
    fake = FakeCrossEncoder({"en iyi sonuç": 5.0, "ikinci": 1.0})
    reranker = Reranker(model=fake)

    result = reranker.rerank_with_safety_net("sorgu", candidates, top_k=2)

    assert [r["chunk_id"] for r in result] == ["c1", "c2"]
    assert "rescued_by_safety_net" not in result[0]


def test_safety_net_empty_candidates_returns_empty():
    fake = FakeCrossEncoder({})
    reranker = Reranker(model=fake)
    assert reranker.rerank_with_safety_net("sorgu", [], top_k=5) == []