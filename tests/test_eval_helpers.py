import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_spec = importlib.util.spec_from_file_location(
    "run_eval", Path(__file__).resolve().parent.parent / "scripts" / "run_eval.py"
)
run_eval = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_eval)


def test_normalize_article_plain_madde():
    assert run_eval._normalize_article("MADDE 9") == ("MADDE", "9")


def test_normalize_article_ek_madde():
    assert run_eval._normalize_article("EK MADDE 5") == ("EK MADDE", "5")


def test_normalize_article_gecici_madde():
    assert run_eval._normalize_article("GEÇİCİ MADDE 6") == ("GEÇİCİ MADDE", "6")


def test_normalize_article_with_slash_number():
    assert run_eval._normalize_article("MADDE 5/A") == ("MADDE", "5/A")


QUESTION_POSITIVE = {
    "expected_documents": ["doc1"],
    "expected_articles": ["MADDE 9"],
}
QUESTION_NEGATIVE = {
    "expected_documents": [],
    "expected_articles": [],
}


def test_check_recall_hit():
    reranked = [{"doc_id": "doc1", "madde_kind": "MADDE", "madde_no": "9"}]
    assert run_eval._check_recall(reranked, QUESTION_POSITIVE) is True


def test_check_recall_miss_wrong_doc():
    reranked = [{"doc_id": "doc2", "madde_kind": "MADDE", "madde_no": "9"}]
    assert run_eval._check_recall(reranked, QUESTION_POSITIVE) is False


def test_check_recall_miss_wrong_madde():
    reranked = [{"doc_id": "doc1", "madde_kind": "MADDE", "madde_no": "10"}]
    assert run_eval._check_recall(reranked, QUESTION_POSITIVE) is False


def test_check_recall_correct_doc_wrong_kind_is_miss():
    """EK MADDE 5 ile MADDE 5 çakışmasın diye kind de eşleşmeli."""
    reranked = [{"doc_id": "doc1", "madde_kind": "EK MADDE", "madde_no": "9"}]
    assert run_eval._check_recall(reranked, QUESTION_POSITIVE) is False


def test_check_recall_negative_question_returns_none():
    reranked = [{"doc_id": "doc1", "madde_kind": "MADDE", "madde_no": "9"}]
    assert run_eval._check_recall(reranked, QUESTION_NEGATIVE) is None


def test_summarize_computes_recall_by_difficulty():
    results = [
        {"is_negative_test": False, "difficulty": "kolay", "recall_hit": True, "recall_rank": 2},
        {"is_negative_test": False, "difficulty": "kolay", "recall_hit": False, "recall_rank": None},
        {"is_negative_test": False, "difficulty": "zor", "recall_hit": True, "recall_rank": 1},
    ]
    summary = run_eval.summarize(results)
    # recall@8 (FINAL_TOP_K) - eskiden yanlislikla "recall_at_5" diye
    # adlandirilan metrik budur (bkz. run_eval.py yorumu).
    assert summary["recall_at_8_kolay"] == 0.5
    assert summary["recall_at_8_zor"] == 1.0
    assert summary["recall_at_8_overall"] == pytest_approx(2 / 3)


def test_summarize_recall_at_k_uses_rank_not_just_hit_flag():
    # rank=6, k=5 icin MISS olmali (recall_hit=True olsa bile, cunku hit
    # FINAL_TOP_K=8 dahilinde ama ilk 5'te degil) - bu, K etiketinin
    # anlamli olmasini saglayan asil davranis degisikligi.
    results = [
        {"is_negative_test": False, "difficulty": "kolay", "recall_hit": True, "recall_rank": 1},
        {"is_negative_test": False, "difficulty": "kolay", "recall_hit": True, "recall_rank": 6},
    ]
    summary = run_eval.summarize(results)
    assert summary["recall_at_1_overall"] == 0.5
    assert summary["recall_at_5_overall"] == 0.5
    assert summary["recall_at_8_overall"] == 1.0


def pytest_approx(x, tol=1e-9):
    class _Approx:
        def __eq__(self, other):
            return abs(other - x) < tol

    return _Approx()


def test_summarize_negative_test_success_rate():
    results = [
        {"is_negative_test": True, "correct_low_confidence": True},
        {"is_negative_test": True, "correct_low_confidence": False},
    ]
    summary = run_eval.summarize(results)
    assert summary["negative_test_success_rate"] == 0.5
    assert summary["negative_test_count"] == 2


def test_summarize_negative_test_prefers_guard_low_confidence_over_retrieval_score():
    # --with-generation ile calistiginda, retrieval skoru (correct_low_confidence)
    # yaniltici olsa bile gercek uretim davranisi (guard_low_confidence) esas alinmali.
    results = [
        # retrieval skoru "basarisiz" diyor ama model gercekte dogru sekilde reddetti
        {
            "is_negative_test": True,
            "correct_low_confidence": False,
            "guard_low_confidence": True,
        },
        # retrieval skoru "basarili" diyor ama model gercekte tam bir cevap uretti
        {
            "is_negative_test": True,
            "correct_low_confidence": True,
            "guard_low_confidence": False,
        },
    ]
    summary = run_eval.summarize(results)
    assert summary["negative_test_success_rate"] == 0.5
    assert summary["negative_test_count"] == 2


def test_summarize_citation_groundedness_when_generation_included():
    results = [
        {
            "is_negative_test": False,
            "difficulty": "kolay",
            "recall_hit": True,
            "total_citation_count": 4,
            "ungrounded_citation_count": 1,
        }
    ]
    summary = run_eval.summarize(results)
    assert summary["citation_groundedness_rate"] == 0.75


def test_summarize_citation_groundedness_skips_records_without_generation():
    results = [
        {"is_negative_test": False, "difficulty": "kolay", "recall_hit": True},
        {
            "is_negative_test": False,
            "difficulty": "kolay",
            "recall_hit": True,
            "total_citation_count": 4,
            "ungrounded_citation_count": 1,
        },
    ]
    summary = run_eval.summarize(results)
    assert summary["citation_groundedness_rate"] == 0.75


def test_find_rank_returns_position_when_first():
    reranked = [{"doc_id": "doc1", "madde_kind": "MADDE", "madde_no": "9"}]
    assert run_eval._find_rank(reranked, QUESTION_POSITIVE) == 1


def test_find_rank_returns_position_when_third():
    reranked = [
        {"doc_id": "docX", "madde_kind": "MADDE", "madde_no": "1"},
        {"doc_id": "docY", "madde_kind": "MADDE", "madde_no": "2"},
        {"doc_id": "doc1", "madde_kind": "MADDE", "madde_no": "9"},
    ]
    assert run_eval._find_rank(reranked, QUESTION_POSITIVE) == 3


def test_find_rank_returns_none_when_not_found():
    reranked = [{"doc_id": "doc2", "madde_kind": "MADDE", "madde_no": "9"}]
    assert run_eval._find_rank(reranked, QUESTION_POSITIVE) is None


def test_find_rank_returns_none_for_negative_question():
    reranked = [{"doc_id": "doc1", "madde_kind": "MADDE", "madde_no": "9"}]
    assert run_eval._find_rank(reranked, QUESTION_NEGATIVE) is None


def test_summarize_computes_mrr():
    results = [
        {"is_negative_test": False, "difficulty": "kolay", "recall_hit": True, "recall_rank": 1},
        {"is_negative_test": False, "difficulty": "kolay", "recall_hit": True, "recall_rank": 4},
        {"is_negative_test": False, "difficulty": "orta", "recall_hit": False, "recall_rank": None},
    ]
    summary = run_eval.summarize(results)
    assert abs(summary["mrr"] - 0.41666666666666663) < 1e-9


def test_summarize_computes_mrr_at_k_caps_ranks_beyond_k():
    # rank=6 icin mrr_at_5 katkisi 0 olmali (5'i asiyor), ama genel mrr'a
    # (k=None, sinirsiz) 1/6 olarak katkida bulunmali.
    results = [
        {"is_negative_test": False, "difficulty": "kolay", "recall_hit": True, "recall_rank": 6},
    ]
    summary = run_eval.summarize(results)
    assert summary["mrr_at_5"] == 0.0
    assert abs(summary["mrr"] - (1 / 6)) < 1e-9
    assert abs(summary["mrr_at_8"] - (1 / 6)) < 1e-9


def test_summarize_computes_average_latencies():
    results = [
        {
            "is_negative_test": False, "difficulty": "kolay", "recall_hit": True,
            "recall_rank": 1, "retrieval_latency_seconds": 0.2, "generation_latency_seconds": 1.0,
        },
        {
            "is_negative_test": False, "difficulty": "kolay", "recall_hit": True,
            "recall_rank": 1, "retrieval_latency_seconds": 0.4, "generation_latency_seconds": 2.0,
        },
    ]
    summary = run_eval.summarize(results)
    assert summary["avg_retrieval_latency_seconds"] == 0.3
    assert summary["avg_generation_latency_seconds"] == 1.5
