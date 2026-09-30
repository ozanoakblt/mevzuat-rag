from pathlib import Path
p = Path("tests/test_eval_helpers.py")
s = p.read_text(encoding="utf-8")

s += """

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
"""

p.write_text(s, encoding="utf-8")
print("Tamamlandi.")
