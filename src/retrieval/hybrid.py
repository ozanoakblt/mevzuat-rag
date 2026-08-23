"""
Faz 6: Hybrid retrieval — Faz 4 (dense/embedding) ve Faz 5 (sparse/BM25)
sonuçlarını Reciprocal Rank Fusion (RRF) ile birleştirir.

RRF neden skor-normalize etmek yerine tercih edildi: Chroma'nın cosine
mesafesi ile BM25 skoru tamamen farklı ölçeklerde (biri 0-2 arası mesafe,
diğeri sınırsız pozitif skor) — bunları "ağırlıklı ortalama" ile birleştirmek
kırılgan ve elle ayarlanacak bir katsayı gerektirir. RRF bunun yerine
sadece SIRALAMAYI kullanır: score = Σ 1/(k + rank). k=60 literatürde
(Cormack et al. 2009) yaygın kullanılan, ayarlama gerektirmeyen bir
varsayılan değerdir.
"""
from __future__ import annotations

DEFAULT_RRF_K = 60


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]], k: int = DEFAULT_RRF_K
) -> dict[str, float]:
    """
    ranked_lists: her biri en alakalıdan en az alakalıya sıralı chunk_id
    listesi (dense sonuçlar, sparse sonuçlar gibi). Bir chunk_id, bazı
    listelerde hiç bulunmayabilir — o listeden katkı almaz.
    """
    scores: dict[str, float] = {}
    for ranked_list in ranked_lists:
        for rank, chunk_id in enumerate(ranked_list, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return scores


def hybrid_search(
    query: str,
    embedder,
    vector_store,
    bm25_index,
    top_k: int = 5,
    retrieve_k: int = 20,
    rrf_k: int = DEFAULT_RRF_K,
) -> list[dict]:
    """
    embedder: src.embedding.embedder.Embedder
    vector_store: src.embedding.vector_store.VectorStore
    bm25_index: src.retrieval.bm25_index.BM25Index
    """
    query_vec = embedder.embed_query(query)
    dense_results = vector_store.query(query_vec, n_results=retrieve_k)
    sparse_results = bm25_index.search(query, top_k=retrieve_k)

    dense_ids = [r["chunk_id"] for r in dense_results]
    sparse_ids = [r["chunk_id"] for r in sparse_results]

    fused_scores = reciprocal_rank_fusion([dense_ids, sparse_ids], k=rrf_k)

    # chunk_id -> tam bilgi (metadata + text), hangi kaynaktan bulunduysa oradan.
    info_by_id: dict[str, dict] = {}
    for r in dense_results:
        info_by_id[r["chunk_id"]] = {
            "text": r["text"],
            **r["metadata"],
            "in_dense": True,
        }
    for r in sparse_results:
        existing = info_by_id.setdefault(
            r["chunk_id"],
            {
                "text": r["text"],
                "doc_id": r.get("doc_id"),
                "madde_kind": r.get("madde_kind"),
                "madde_no": r.get("madde_no"),
                "madde_baslik": r.get("madde_baslik"),
                "bolum": r.get("bolum"),
                "fikra_no": r.get("fikra_no"),
                "bent_no": r.get("bent_no"),
                "section": r.get("section"),
            },
        )
        existing["in_sparse"] = True

    ranked_ids = sorted(fused_scores.keys(), key=lambda cid: fused_scores[cid], reverse=True)

    results = []
    for chunk_id in ranked_ids[:top_k]:
        info = info_by_id[chunk_id]
        results.append(
            {
                "chunk_id": chunk_id,
                "rrf_score": fused_scores[chunk_id],
                "in_dense": info.get("in_dense", False),
                "in_sparse": info.get("in_sparse", False),
                **info,
            }
        )
    return results
