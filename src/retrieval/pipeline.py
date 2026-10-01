"""
Faz 13: Tek bir ortak retrieval pipeline'i.

Eskiden bu mantigin (query expansion + per-subquery hybrid search +
guard_pool round-robin + rerank + EK kardes-chunk kurtarma) IKI AYRI
kopyasi vardi: web/app.py ve scripts/run_eval.py. Bu, gercek bir
surukleme (drift) sorununa yol acmisti - orn. doc-type boost mantigi
SADECE web/app.py'de vardi, run_eval.py'de hic yoktu (yani eval sonuclari
canli uygulamanin gercek davranisini yansitmiyordu). scripts/sync_eval_*.py
altindaki tek seferlik "yama" scriptleri de bu driftin gecmiste gercekten
yasandiginin kaniti. Artik HER IKI cagri yeri de bu modulu kullaniyor.

NOT (denendi, geri alindi): "adaptive query expansion" - ilk-gecis
(expansion'siz) rerank skoru belirli bir esigin ustundeyse expansion'i
atlama fikri - ampirik olarak test edildi ve TERK EDILDI. 92 soruluk eval
kosusunda orijinal 46 sorunun recall@8'i %95.65'ten %84.78'e dustu (7 soru
regrese oldu); sebebi, cross-encoder rerank skorunun "bu pasaj sorguyla
ALAKALI mi" sorusuna iyi cevap verip "bu DOGRU pasaj mi" sorusuna
GUVENILMEZ bir proxy olmasi - dogru bulunan sorularin skor dagilimi
(0.18-10.89) ile yanlis-ama-ilgili bulunan sorularin dagilimi (0.15-8.43)
neredeyse tamamen cakisiyordu, hicbir esik ikisini ayiramadi. Bu yuzden
retrieve() HER ZAMAN tam (expansion'li) pipeline'i calistirir.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .hybrid import hybrid_search
from .query_expansion import QUERY_TYPE_PREFERRED_DOC_TYPES, expand_query, get_query_type
from .temporal import apply_temporal_adjustment, extract_query_date

CANDIDATE_POOL_SIZE = 30
# 8'den 10'a cikarildi: korpusa 2 yeni Kurul Karari belgesi eklenince
# (teknik kalite bedeli + serbest tuketici limiti 2026), aday havuzundaki
# rekabet hafifce artti ve 5 soru (q10/q13/q19/q27/q41) daha once 7-8.
# sirada bulunan dogru pasaji artik 9-14. siraya itiyordu - kod hatasi
# degil, sabit bir top-K kesiminin korpus buyumesiyle dogal yan etkisi.
# 92 soruluk eval kosusunda dogrulandi: 10'a cikarinca bu 5 soru da
# tekrar kapsaniyor.
FINAL_TOP_K = 10
# guard_pool round-robin derinligi - bkz. eski run_eval.py yorumu (artik
# burada): 52 soruluk retrieval-only sweep'te derinlik 1 -> recall %87.0,
# derinlik 8 -> %95.65, 13'e cikmanin ek faydasi yok (8'de plato).
GUARD_ROUND_ROBIN_DEPTH = 8
DOC_TYPE_BOOST_MULTIPLIER = 1.5


@dataclass
class RetrievalResult:
    chunks: list[dict]
    query_type: str | None
    sub_queries: list[str] = field(default_factory=list)


def _attach_ek_siblings(reranked: list[dict], candidates: list[dict]) -> list[dict]:
    """
    Final listede EK (ek madde/tablo) turunde bir chunk secildiyse, ayni
    ek'in DIGER parcalarini da (bolunmus olabilir) ekler - aksi halde
    model ekin sadece bir kismini gorup eksik/yanlis cevap verebilir.
    """
    existing_ids = {c["chunk_id"] for c in reranked}
    ek_keys_selected = {
        (c["doc_id"], c["madde_no"]) for c in reranked if c.get("madde_kind") == "EK"
    }
    if not ek_keys_selected:
        return reranked
    extra_ek_chunks = [
        c
        for c in candidates
        if c.get("madde_kind") == "EK"
        and (c["doc_id"], c["madde_no"]) in ek_keys_selected
        and c["chunk_id"] not in existing_ids
    ]
    if not extra_ek_chunks:
        return reranked
    for c in extra_ek_chunks:
        c.setdefault("rerank_score", 0.0)
    return reranked + extra_ek_chunks


def retrieve(
    question: str,
    embedder,
    vector_store,
    bm25_index,
    reranker,
    doc_types: dict[str, str] | None = None,
    doc_versions: dict[str, tuple[str, date]] | None = None,
) -> RetrievalResult:
    """
    doc_types: {doc_id: doc_type} - verilirse ve soru "guncel_deger" tipi
    cikarsa, tercih edilen doc_type'lardaki (orn. "karar") sonuclarin
    rrf_score'u DOC_TYPE_BOOST_MULTIPLIER ile carpilir.

    doc_versions: {doc_id: (version_group, effective_from)} - verilirse,
    ayni version_group'u paylasan (orn. bir yonetmeligin konsolide metni
    + degisikligi) adaylar arasinda sorudan cikarilan tarihe (ya da tarih
    yoksa "en guncel versiyon" varsayilanina) gore one cikarma/geri plana
    itme uygulanir (bkz. src/retrieval/temporal.py).
    """
    sub_queries = expand_query(question, embedder=embedder)
    query_type = get_query_type(question, embedder=embedder)
    preferred_doc_types = QUERY_TYPE_PREFERRED_DOC_TYPES.get(query_type, [])
    query_date = extract_query_date(question) if doc_versions else None

    candidates_by_id: dict[str, dict] = {}
    per_query_results: list[list[dict]] = []
    for sq in sub_queries:
        sq_results = hybrid_search(
            sq, embedder, vector_store, bm25_index, top_k=CANDIDATE_POOL_SIZE
        )
        if doc_types and preferred_doc_types:
            for r in sq_results:
                if doc_types.get(r.get("doc_id")) in preferred_doc_types:
                    r["rrf_score"] *= DOC_TYPE_BOOST_MULTIPLIER
        if doc_versions:
            apply_temporal_adjustment(sq_results, query_date, doc_versions)
        if (doc_types and preferred_doc_types) or doc_versions:
            sq_results.sort(key=lambda r: r["rrf_score"], reverse=True)
        per_query_results.append(sq_results)
        for r in sq_results:
            cid = r["chunk_id"]
            if cid not in candidates_by_id or r["rrf_score"] > candidates_by_id[cid]["rrf_score"]:
                candidates_by_id[cid] = r

    # Round-robin guard_pool: her alt-sorgunun EN IYI sonucunu (rank 1) once
    # ekleyerek, hicbir alt-sorgunun kendi ust siralarini tek basina one
    # gecirip digerlerini bogmasini onluyoruz (gercek bir subquery-acligi
    # vakasinda eklendi). rerank_with_safety_net APPEND semantigine sahip
    # (gercek sonuclari SILMEZ, sadece eksik olanlari sona ekler) - bu
    # yuzden derinligi buyutmenin recall acisindan riski yok.
    guard_ids: list[str] = []
    for i in range(GUARD_ROUND_ROBIN_DEPTH):
        for sq_results in per_query_results:
            if i < len(sq_results):
                cid = sq_results[i]["chunk_id"]
                if cid not in guard_ids:
                    guard_ids.append(cid)

    candidates = sorted(candidates_by_id.values(), key=lambda c: c["rrf_score"], reverse=True)
    guard_pool = [candidates_by_id[cid] for cid in guard_ids]
    reranked = reranker.rerank_with_safety_net(
        question, candidates, top_k=FINAL_TOP_K, guard_pool=guard_pool
    )
    chunks = _attach_ek_siblings(reranked, candidates)
    return RetrievalResult(chunks=chunks, query_type=query_type, sub_queries=sub_queries)
