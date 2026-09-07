import pathlib

p = pathlib.Path("web/app.py")
text = p.read_text(encoding="utf-8")

old = """    sub_queries = expand_query(question)
    candidates_by_id: dict[str, dict] = {}
    guard_ids: list[str] = []
    for sq in sub_queries:
        sq_results = hybrid_search(
            sq,
            _state["embedder"],
            vector_store,
            _state["bm25_index"],
            top_k=CANDIDATE_POOL_SIZE,
        )
        for i, r in enumerate(sq_results):
            cid = r["chunk_id"]
            if cid not in candidates_by_id or r["rrf_score"] > candidates_by_id[cid]["rrf_score"]:
                candidates_by_id[cid] = r
            if i < 13 and cid not in guard_ids:
                guard_ids.append(cid)"""

new = """    sub_queries = expand_query(question)
    candidates_by_id: dict[str, dict] = {}
    per_query_results: list[list[dict]] = []
    for sq in sub_queries:
        sq_results = hybrid_search(
            sq,
            _state["embedder"],
            vector_store,
            _state["bm25_index"],
            top_k=CANDIDATE_POOL_SIZE,
        )
        per_query_results.append(sq_results)
        for r in sq_results:
            cid = r["chunk_id"]
            if cid not in candidates_by_id or r["rrf_score"] > candidates_by_id[cid]["rrf_score"]:
                candidates_by_id[cid] = r

    # Round-robin (nobetlese) oncelik: her alt-sorunun ayni siradaki
    # sonucunu once ekleyerek, hicbir alt-sorunun kendi ust siralarini
    # (orn. ilk 13'unu) tek basina one gecirip diger alt-sorularin
    # gercekten alakali ama daha az bilinen sonuclarini "kuyrukta"
    # boguntmasini onluyoruz (gercek vakada tespit edildi: subquery1'in
    # top-13'u guard_pool'un basini kapatinca, subquery3'un cok daha
    # alakali bir sonucu final listeye hic giremiyordu).
    guard_ids: list[str] = []
    max_len = max((len(r) for r in per_query_results), default=0)
    for i in range(min(max_len, 13)):
        for sq_results in per_query_results:
            if i < len(sq_results):
                cid = sq_results[i]["chunk_id"]
                if cid not in guard_ids:
                    guard_ids.append(cid)"""

count = text.count(old)
print("Kac yer eslesti:", count)
if count == 1:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("Basarili.")
else:
    print("HATA, elle kontrol gerekli.")
