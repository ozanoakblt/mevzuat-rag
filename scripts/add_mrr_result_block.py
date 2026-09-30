from pathlib import Path
p = Path("scripts/run_eval.py")
s = p.read_text(encoding="utf-8")

old_result_block = """    is_negative_test = not question["expected_documents"]
    best_score = max((c["rerank_score"] for c in reranked), default=None)

    result = {
        "id": question["id"],
        "difficulty": question["difficulty"],
        "is_negative_test": is_negative_test,
        "best_rerank_score": best_score,
    }

    if is_negative_test:
        # Başarı = düşük güven göstermek (sistem doğru şekilde "bulamadım" davranışında)
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
        # Başarı = düşük güven göstermek (sistem doğru şekilde "bulamadım" davranışında)
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

assert old_result_block in s, "hala eslesmedi - dosyanin guncel halini gonder"
s = s.replace(old_result_block, new_result_block)
p.write_text(s, encoding="utf-8")
print("Tamamlandi: result blogu eklendi.")
