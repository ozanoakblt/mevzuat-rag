import sys
from pathlib import Path
sys.path.insert(0, str(Path(".").resolve()))
from dotenv import load_dotenv
load_dotenv()

from src.embedding.embedder import Embedder
from src.embedding.vector_store import VectorStore, load_all_chunks
from src.retrieval.bm25_index import BM25Index
from src.retrieval.hybrid import hybrid_search
from src.retrieval.query_expansion import expand_query
from src.retrieval.reranker import Reranker

ROOT = Path(".").resolve()
chunks = load_all_chunks(ROOT / "data" / "processed")
embedder = Embedder()
vector_store = VectorStore(persist_dir=ROOT / "data" / "vector_store")
bm25_index = BM25Index(chunks)
reranker = Reranker()

def is_target(r):
    return r.get("doc_id") == "yonetmelik-sebeke" and str(r.get("madde_no", "")).startswith("Ek-18")

question = "Dağıtım şirketleri inverterlara set point gönderebiliyor mu?"
sub_queries = expand_query(question)
print("Alt sorular:")
for sq in sub_queries:
    print(" -", sq)

candidates_by_id = {}
guard_ids = []
for sq in sub_queries:
    print(f"\n--- ALT-SORU: {sq}")
    sq_results = hybrid_search(sq, embedder, vector_store, bm25_index, top_k=30)
    found_at = None
    for i, r in enumerate(sq_results):
        cid = r["chunk_id"]
        if cid not in candidates_by_id or r["rrf_score"] > candidates_by_id[cid]["rrf_score"]:
            candidates_by_id[cid] = r
        if i < 8 and cid not in guard_ids:
            guard_ids.append(cid)
        if is_target(r) and found_at is None:
            found_at = i
    print(f"  Ek-18 top-30'da bulundu mu: {found_at is not None} (index: {found_at})")

candidates = sorted(candidates_by_id.values(), key=lambda c: c["rrf_score"], reverse=True)
guard_pool = [candidates_by_id[cid] for cid in guard_ids]

print("\nEk-18 candidates icinde mi:", any(is_target(c) for c in candidates))
print("Ek-18 guard_pool icinde mi:", any(is_target(c) for c in guard_pool))
