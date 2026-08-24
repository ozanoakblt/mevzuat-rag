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

CANDIDATE_POOL_SIZE = 30
FINAL_TOP_K = 8

def is_target(r):
    return r.get("madde_no") == "10/A" and r.get("fikra_no") == "4" and r.get("bent_no") == "a"

question = "Bağlantı görüşü geçerlilik süresi kaç gün?"
sub_queries = expand_query(question)
print("Alt sorular:", sub_queries)

candidates_by_id = {}
guard_ids = []
for sq in sub_queries:
    sq_results = hybrid_search(sq, embedder, vector_store, bm25_index, top_k=CANDIDATE_POOL_SIZE)
    for i, r in enumerate(sq_results):
        cid = r["chunk_id"]
        if cid not in candidates_by_id or r["rrf_score"] > candidates_by_id[cid]["rrf_score"]:
            candidates_by_id[cid] = r
        if i < 5 and cid not in guard_ids:
            guard_ids.append(cid)

candidates = sorted(candidates_by_id.values(), key=lambda c: c["rrf_score"], reverse=True)
guard_pool = [candidates_by_id[cid] for cid in guard_ids]

print("\nHedef candidates icinde mi:", any(is_target(c) for c in candidates))
print("Hedef guard_pool icinde mi:", any(is_target(c) for c in guard_pool))
print("guard_pool boyutu:", len(guard_pool))

top_chunks = reranker.rerank_with_safety_net(question, candidates, top_k=FINAL_TOP_K, guard_pool=guard_pool)
print("\nHedef final top_chunks icinde mi:", any(is_target(c) for c in top_chunks))
print("\nFinal liste:")
for c in top_chunks:
    marker = " <-- HEDEF" if is_target(c) else ""
    print(f"  Madde {c.get('madde_no')} fikra {c.get('fikra_no')} bent {c.get('bent_no')} (rerank={c['rerank_score']:.4f}){marker}")
