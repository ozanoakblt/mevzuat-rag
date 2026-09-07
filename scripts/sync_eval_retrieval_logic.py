import pathlib

p = pathlib.Path("scripts/run_eval.py")
text = p.read_text(encoding="utf-8")

old = """    candidates = hybrid_search(
        question["question"], embedder, vector_store, bm25_index, top_k=CANDIDATE_POOL_SIZE
    )
    reranked = reranker.rerank_with_safety_net(question["question"], candidates, top_k=FINAL_TOP_K)"""

new = """    q_text = question["question"]
    sub_queries = expand_query(q_text)
    candidates_by_id: dict[str, dict] = {}
    guard_ids: list[str] = []
    for sq in sub_queries:
        sq_results = hybrid_search(sq, embedder, vector_store, bm25_index, top_k=CANDIDATE_POOL_SIZE)
        for i, r in enumerate(sq_results):
            cid = r["chunk_id"]
            if cid not in candidates_by_id or r["rrf_score"] > candidates_by_id[cid]["rrf_score"]:
                candidates_by_id[cid] = r
            if i < 8 and cid not in guard_ids:
                guard_ids.append(cid)
    candidates = sorted(candidates_by_id.values(), key=lambda c: c["rrf_score"], reverse=True)
    guard_pool = [candidates_by_id[cid] for cid in guard_ids]
    reranked = reranker.rerank_with_safety_net(
        q_text, candidates, top_k=FINAL_TOP_K, guard_pool=guard_pool
    )

    existing_ids = {c["chunk_id"] for c in reranked}
    ek_keys_selected = {
        (c["doc_id"], c["madde_no"]) for c in reranked if c.get("madde_kind") == "EK"
    }
    if ek_keys_selected:
        extra_ek_chunks = [
            c for c in candidates
            if c.get("madde_kind") == "EK"
            and (c["doc_id"], c["madde_no"]) in ek_keys_selected
            and c["chunk_id"] not in existing_ids
        ]
        if extra_ek_chunks:
            for c in extra_ek_chunks:
                c.setdefault("rerank_score", 0.0)
            reranked = reranked + extra_ek_chunks
            existing_ids.update(c["chunk_id"] for c in extra_ek_chunks)"""

count = text.count(old)
print("Retrieval mantigi - kac yer eslesti:", count)
if count == 1:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("Basarili.")
else:
    print("HATA, elle kontrol gerekli.")
