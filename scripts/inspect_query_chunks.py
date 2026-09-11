"""
Bir soru icin, generate_answer'a GIDEN chunk'lari (1'den baslayan, model
promptundaki [1], [2]... numaralandirmasiyla BIREBIR eslesecek sekilde)
ekrana basar.

Kullanim:
    python scripts/inspect_query_chunks.py --question "Soru metni buraya"
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
from src.retrieval.bm25_index import BM25Index
from src.retrieval.hybrid import hybrid_search
from src.retrieval.query_expansion import expand_query
from src.retrieval.reranker import Reranker

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
VECTOR_STORE_DIR = Path(__file__).resolve().parent.parent / "data" / "vector_store"
CANDIDATE_POOL_SIZE = 20
FINAL_TOP_K = 8


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", type=str, required=True)
    args = parser.parse_args()

    chunks = load_all_chunks(PROCESSED_DIR)
    embedder = Embedder()
    vector_store = VectorStore(persist_dir=VECTOR_STORE_DIR)
    bm25_index = BM25Index(chunks)
    reranker = Reranker()

    q_text = args.question
    sub_queries = expand_query(q_text)
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

    print(f"Toplam {len(reranked)} chunk model promptuna gidiyor:\n")
    for i, c in enumerate(reranked, 1):
        print(f"===== [{i}] doc_id={c.get('doc_id')} madde_no={c.get('madde_no')} rerank_score={c.get('rerank_score')} =====")
        print(c["text"])
        print()


if __name__ == "__main__":
    main()
