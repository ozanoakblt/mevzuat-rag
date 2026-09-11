"""
web/app.py'nin /api/ask endpoint'iyle BIREBIR ayni retrieval + generation
pipeline'ini calistirip, HAM cevabi (frontend'in gizledigi "Kaynak
Alıntıları:" bolumu dahil) ve guard uyarilarini terminale basar.

Kullanim:
    python scripts/ask_full.py --question "Soru metni buraya"
"""
from __future__ import annotations

import argparse
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

CANDIDATE_POOL_SIZE = 30
FINAL_TOP_K = 8

DOC_TITLES = {s.doc_id: s.title for s in SOURCES}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", type=str, required=True)
    args = parser.parse_args()
    question = args.question

    chunks = load_all_chunks(PROCESSED_DIR)
    embedder = Embedder()
    vector_store = VectorStore(persist_dir=VECTOR_STORE_DIR)
    bm25_index = BM25Index(chunks)
    reranker = Reranker()

    sub_queries = expand_query(question)
    print(f"Alt-sorular: {sub_queries}\n")

    candidates_by_id: dict[str, dict] = {}
    per_query_results: list[list[dict]] = []
    for sq in sub_queries:
        sq_results = hybrid_search(sq, embedder, vector_store, bm25_index, top_k=CANDIDATE_POOL_SIZE)
        per_query_results.append(sq_results)
        for r in sq_results:
            cid = r["chunk_id"]
            if cid not in candidates_by_id or r["rrf_score"] > candidates_by_id[cid]["rrf_score"]:
                candidates_by_id[cid] = r

    guard_ids: list[str] = []
    max_len = max((len(r) for r in per_query_results), default=0)
    for i in range(min(max_len, 13)):
        for sq_results in per_query_results:
            if i < len(sq_results):
                cid = sq_results[i]["chunk_id"]
                if cid not in guard_ids:
                    guard_ids.append(cid)
    candidates = sorted(candidates_by_id.values(), key=lambda c: c["rrf_score"], reverse=True)
    guard_pool = [candidates_by_id[cid] for cid in guard_ids]
    top_chunks = reranker.rerank_with_safety_net(
        question, candidates, top_k=FINAL_TOP_K, guard_pool=guard_pool
    )

    existing_ids = {c["chunk_id"] for c in top_chunks}
    ek_keys_selected = {
        (c["doc_id"], c["madde_no"]) for c in top_chunks if c.get("madde_kind") == "EK"
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
            top_chunks = top_chunks + extra_ek_chunks

    print(f"Toplam {len(top_chunks)} chunk model promptuna gidiyor.\n")
    print("Cevap üretiliyor...\n")
    answer = generate_answer(question, top_chunks, doc_titles=DOC_TITLES)

    guard = run_guard(answer, top_chunks)
    warnings = format_guard_warnings(guard)

    print("=" * 70)
    print("HAM CEVAP (Kaynak Alıntıları dahil, web arayüzünün gizlediği hali):")
    print("=" * 70)
    print(answer)
    print()
    if warnings:
        print("=" * 70)
        print(warnings)


if __name__ == "__main__":
    main()
