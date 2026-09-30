from pathlib import Path
p = Path("scripts/run_eval.py")
s = p.read_text(encoding="utf-8")

old_import = "from src.retrieval.reranker import Reranker"
new_import = "import time\n\nfrom src.retrieval.reranker import Reranker"
assert old_import in s
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
        return None
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

assert old_check in s
s = s.replace(old_check, new_check)

old_body = """def run_single_question(
    question: dict, embedder, vector_store, bm25_index, reranker, with_generation: bool
) -> dict:
    q_text = question["question"]
    sub_queries = expand_query(q_text, embedder=embedder)"""
new_body = """def run_single_question(
    question: dict, embedder, vector_store, bm25_index, reranker, with_generation: bool
) -> dict:
    retrieval_start = time.perf_counter()
    q_text = question["question"]
    sub_queries = expand_query(q_text, embedder=embedder)"""
assert old_body in s
s = s.replace(old_body, new_body)

old_result_block = """    is_negative_test = not question["expected_documents"]
    best_score = max((c["rerank_score"] for c in reranked), default=None)

    result = {
        "id": question["id"],
        "difficulty": question["difficulty"],
        "is_negative_test": is_negative_test,
        "best_rerank_score": best_score,
    }

    if is_negative_test:
        result["correct_low_confidence"] = (
            best_score is not None and best_score < LOW_CONFIDENCE_RERANK_THRESHOLD
        )
    else:
        result["recall_hit"] = _check_recall(reranked, question)

    if with_generation:
        answer, finish_reason = generate_answer(
            q_text, reranked, doc_titles=DOC_TITLES, return_finish_reason=True
        )
        guard = run_guard(answer, reranked)
        result["guard_low_confidence"] = guard.is_low_confidence
        result["ungrounded_citation_count"] = sum(
            1 for c in guard.citation_checks if not c.grounded
        )
        result["total_citation_count"] = len(guard.citation_checks)
        result["finish_reason"] = finish_reason
        result["answer_text"] = answer

    return result"""

new_result_block = """    retrieval_latency = time.perf_counter() - retrieval_start

    is_negative_test = not question["expected_documents"]
    best_score = max((c["rerank_score"] for c in reranked), default=None)

    result = {
        "id": question["id"],
        "difficulty": question["difficulty"],
        "is_negative_test": is_negative_test,
        "best_rerank_score": best_score,
        "retrieval_latency_seconds": round(retrieval_latency, 3),
    }

    if is_negative_test:
        result["correct_low_confidence"] = (
            best_score is not None and best_score < LOW_CONFIDENCE_RERANK_THRESHOLD
        )
    else:
        result["recall_hit"] = _check_recall(reranked, question)
        result["recall_rank"] = _find_rank(reranked, question)

    if with_generation:
        generation_start = time.perf_counter()
        answer, finish_reason = generate_answer(
            q_text, reranked, doc_titles=DOC_TITLES, return_finish_reason=True
        )
        result["generation_latency_seconds"] = round(time.perf_counter() - generation_start, 3)
        guard = run_guard(answer, reranked)
        result["guard_low_confidence"] = guard.is_low_confidence
        result["ungrounded_citation_count"] = sum(
            1 for c in guard.citation_checks if not c.grounded
        )
        result["total_citation_count"] = len(guard.citation_checks)
        result["finish_reason"] = finish_reason
        result["answer_text"] = answer

    return result"""

assert old_result_block in s
s = s.replace(old_result_block, new_result_block)

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

assert old_summary in s
s = s.replace(old_summary, new_summary)

p.write_text(s, encoding="utf-8")
print("Tamamlandi: MRR + gecikme metrikleri eklendi.")
