from pathlib import Path
p = Path("scripts/run_eval.py")
s = p.read_text(encoding="utf-8")

old_import = "from src.retrieval.reranker import Reranker"
new_import = "import time\n\nfrom src.retrieval.reranker import Reranker"
assert old_import in s, "import satiri bulunamadi"
s = s.replace(old_import, new_import, 1)

old_check = """def _check_recall(reranked: list[dict], question: dict) -> bool:
    expected_docs = set(question["expected_documents"])
    expected_articles = {_normalize_article(a) for a in question["expected_articles"]}
    if not expected_docs:
        return None  # negatif test sorusu, recall@K uygulanmaz
    for chunk in reranked:
        if chunk["doc_id"] in expected_docs:
            if (chunk.get("madde_kind"), chunk.get("madde_no")) in expected_articles:
                return True
    return False"""

new_check = """def _check_recall(reranked: list[dict], question: dict) -> bool:
    expected_docs = set(question["expected_documents"])
    expected_articles = {_normalize_article(a) for a in question["expected_articles"]}
    if not expected_docs:
        return None  # negatif test sorusu, recall@K uygulanmaz
    for chunk in reranked:
        if chunk["doc_id"] in expected_docs:
            if (chunk.get("madde_kind"), chunk.get("madde_no")) in expected_articles:
                return True
    return False


def _find_rank(reranked: list[dict], question: dict) -> int | None:
    \"\"\"Dogru maddenin reranked listesindeki 1-tabanli konumunu doner (MRR icin).\"\"\"
    expected_docs = set(question["expected_documents"])
    expected_articles = {_normalize_article(a) for a in question["expected_articles"]}
    if not expected_docs:
        return None
    for i, chunk in enumerate(reranked, 1):
        if chunk["doc_id"] in expected_docs:
            if (chunk.get("madde_kind"), chunk.get("madde_no")) in expected_articles:
                return i
    return None"""

assert old_check in s, "_check_recall bulunamadi"
s = s.replace(old_check, new_check)

old_summary = """    if positive:
        hits = sum(1 for r in positive if r["recall_hit"])
        summary["recall_at_5_overall"] = hits / len(positive)
        for diff in ("kolay", "orta", "zor"):
            subset = [r for r in positive if r["difficulty"] == diff]
            if subset:
                sub_hits = sum(1 for r in subset if r["recall_hit"])
                summary[f"recall_at_5_{diff}"] = sub_hits / len(subset)"""

new_summary = """    if positive:
        hits = sum(1 for r in positive if r["recall_hit"])
        summary["recall_at_5_overall"] = hits / len(positive)
        for diff in ("kolay", "orta", "zor"):
            subset = [r for r in positive if r["difficulty"] == diff]
            if subset:
                sub_hits = sum(1 for r in subset if r["recall_hit"])
                summary[f"recall_at_5_{diff}"] = sub_hits / len(subset)
        reciprocal_ranks = [
            (1.0 / r["recall_rank"]) if r.get("recall_rank") else 0.0
            for r in positive
        ]
        summary["mrr"] = sum(reciprocal_ranks) / len(reciprocal_ranks)

    retrieval_latencies = [
        r["retrieval_latency_seconds"] for r in results if "retrieval_latency_seconds" in r
    ]
    if retrieval_latencies:
        summary["avg_retrieval_latency_seconds"] = round(
            sum(retrieval_latencies) / len(retrieval_latencies), 3
        )
    generation_latencies = [
        r["generation_latency_seconds"] for r in results if "generation_latency_seconds" in r
    ]
    if generation_latencies:
        summary["avg_generation_latency_seconds"] = round(
            sum(generation_latencies) / len(generation_latencies), 3
        )"""

assert old_summary in s, "summarize positive blogu bulunamadi"
s = s.replace(old_summary, new_summary)

p.write_text(s, encoding="utf-8")
print("Tamamlandi: import + _find_rank + summarize MRR/gecikme eklendi.")
