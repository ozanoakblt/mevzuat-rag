"""
Yonetici sinavindaki supheli/celiskili gorunen sorular icin ek dogrulama
sorularini toplu calistirir.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.embedding.embedder import Embedder
from src.embedding.vector_store import VectorStore, load_all_chunks
from src.generation.answer_generator import generate_answer
from src.generation.citation_guard import format_guard_warnings, run_guard
from src.ingestion.sources import SOURCES
from src.retrieval.bm25_index import BM25Index
from src.retrieval.hybrid import hybrid_search
from src.retrieval.query_expansion import expand_query
from src.retrieval.reranker import Reranker

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
VECTOR_STORE_DIR = ROOT / "data" / "vector_store"
OUTPUT_PATH = ROOT / "scripts" / "exam_followup_sonuclari.txt"

CANDIDATE_POOL_SIZE = 30
FINAL_TOP_K = 8

DOC_TITLES = {s.doc_id: s.title for s in SOURCES}

QUESTIONS = [
    (
        "Q40-celiski",
        "Teknik kaliteyi bozan unsurlarin (genel) giderilmesi icin verilen "
        "sure ile harmonik bozulmaya neden olan kullaniciya verilen "
        "duzeltme suresi ayni hukum mudur, yoksa farkli maddeler mi? "
        "Ikisini ayri ayri, madde numaralariyla birlikte aciklayin.",
    ),
    (
        "Q33-guncellik",
        "Elektrik dagitim sisteminden kaynaklanan kalite sorunu nedeniyle "
        "cihazi zarar goren kullanicinin dagitim sirketine basvuru suresi "
        "kac gundur? Farkli yonetmeliklerde farkli sureler (30 gun, 10 is "
        "gunu) geciyorsa, hangisi GUNCEL ve YURURLUKTE olan hukumdur, "
        "hangisi mulga/eski?",
    ),
    (
        "Q15-16-bedel",
        "2026 yilinda S sinifi ve A sinifi teknik kalite olcumunun AG ve "
        "OG seviyesindeki guncel TL bedelleri nedir? Kurul karariyla "
        "belirlenen guncel tarife degerlerini arayin.",
    ),
    (
        "Q5-serbest-tuketici-limiti",
        "2026 yili icin serbest tuketici limiti kac kWh/yildir? Bu limit "
        "Akilli Sayac PRO icin kullanilan 10 MWh limitiyle ayni midir?",
    ),
]


def main() -> None:
    chunks = load_all_chunks(PROCESSED_DIR)
    embedder = Embedder()
    vector_store = VectorStore(persist_dir=VECTOR_STORE_DIR)
    bm25_index = BM25Index(chunks)
    reranker = Reranker()

    lines = []

    for label, question in QUESTIONS:
        print(f"[{label}] isleniyor...")
        sub_queries = expand_query(question, embedder=embedder)

        candidates_by_id = {}
        per_query_results = []
        for sq in sub_queries:
            sq_results = hybrid_search(sq, embedder, vector_store, bm25_index, top_k=CANDIDATE_POOL_SIZE)
            per_query_results.append(sq_results)
            for r in sq_results:
                cid = r["chunk_id"]
                if cid not in candidates_by_id or r["rrf_score"] > candidates_by_id[cid]["rrf_score"]:
                    candidates_by_id[cid] = r

        guard_ids = []
        max_len = max((len(r) for r in per_query_results), default=0)
        for i in range(min(max_len, 13)):
            for sq_results in per_query_results:
                if i < len(sq_results):
                    cid = sq_results[i]["chunk_id"]
                    if cid not in guard_ids:
                        guard_ids.append(cid)
        candidates = sorted(candidates_by_id.values(), key=lambda c: c["rrf_score"], reverse=True)
        guard_pool = [candidates_by_id[cid] for cid in guard_ids]
        top_chunks = reranker.rerank_with_safety_net(question, candidates, top_k=FINAL_TOP_K, guard_pool=guard_pool)

        existing_ids = {c["chunk_id"] for c in top_chunks}
        ek_keys_selected = {(c["doc_id"], c["madde_no"]) for c in top_chunks if c.get("madde_kind") == "EK"}
        if ek_keys_selected:
            extra_ek_chunks = [
                c for c in candidates
                if c.get("madde_kind") == "EK" and (c["doc_id"], c["madde_no"]) in ek_keys_selected
                and c["chunk_id"] not in existing_ids
            ]
            if extra_ek_chunks:
                for c in extra_ek_chunks:
                    c.setdefault("rerank_score", 0.0)
                top_chunks = top_chunks + extra_ek_chunks

        answer = generate_answer(question, top_chunks, doc_titles=DOC_TITLES)
        guard = run_guard(answer, top_chunks)
        warnings = format_guard_warnings(guard)

        lines.append("=" * 70)
        lines.append(f"[{label}]")
        lines.append(f"SORU: {question}")
        lines.append("-" * 70)
        lines.append(answer)
        if warnings:
            lines.append("-" * 70)
            lines.append(warnings)
        lines.append("")

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nTamamlandi. Sonuclar: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
