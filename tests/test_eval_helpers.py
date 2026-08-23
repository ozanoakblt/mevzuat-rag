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
        {"is_negative_test": False, "difficulty": "kolay", "recall_hit": True},
        {"is_negative_test": False, "difficulty": "kolay", "recall_hit": False},
        {"is_negative_test": False, "difficulty": "zor", "recall_hit": True},
    ]
    summary = run_eval.summarize(results)
    assert summary["recall_at_5_kolay"] == 0.5
    assert summary["recall_at_5_zor"] == 1.0
    assert summary["recall_at_5_overall"] == pytest_approx(2 / 3)


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
