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
    return r.get("madde_no") == "10/A" and r.get("fikra_no") == "4" and r.get("bent_no") == "a"

question = "Bağlantı görüşü geçerlilik süresi kaç gün?"
sub_queries = expand_query(question)

candidates_by_id = {}
guard_ids = []
for sq in sub_queries:
    sq_results = hybrid_search(sq, embedder, vector_store, bm25_index, top_k=30)
    for i, r in enumerate(sq_results):
        cid = r["chunk_id"]
        if cid not in candidates_by_id or r["rrf_score"] > candidates_by_id[cid]["rrf_score"]:
            candidates_by_id[cid] = r
        if i < 5 and cid not in guard_ids:
            guard_ids.append(cid)

candidates = sorted(candidates_by_id.values(), key=lambda c: c["rrf_score"], reverse=True)
guard_pool = [candidates_by_id[cid] for cid in guard_ids]

print("guard_pool sirasi:")
for i, c in enumerate(guard_pool):
    marker = " <-- HEDEF" if is_target(c) else ""
    print(f"  [{i}] Madde {c.get('madde_no')} f{c.get('fikra_no')} bent {c.get('bent_no')}{marker}")

# Manuel olarak rerank_with_safety_net icini izleyelim
reranked = reranker.rerank(question, candidates, top_k=8)
reranked_ids = {r["chunk_id"] for r in reranked}
print("\nOn-rerank top-8 (rescue oncesi):")
for c in reranked:
    marker = " <-- HEDEF" if is_target(c) else ""
    print(f"  Madde {c.get('madde_no')} f{c.get('fikra_no')} bent {c.get('bent_no')} (score={c['rerank_score']:.4f}){marker}")

missing = [c for c in guard_pool if c["chunk_id"] not in reranked_ids]
print(f"\nmissing listesi ({len(missing)} eleman):")
for i, c in enumerate(missing):
    marker = " <-- HEDEF" if is_target(c) else ""
    print(f"  [{i}] Madde {c.get('madde_no')} f{c.get('fikra_no')} bent {c.get('bent_no')}{marker}")
