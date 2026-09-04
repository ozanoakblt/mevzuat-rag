import sys
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

from src.embedding.embedder import Embedder
from src.embedding.vector_store import VectorStore, load_all_chunks
from src.retrieval.bm25_index import BM25Index
from src.retrieval.hybrid import hybrid_search
from src.retrieval.reranker import Reranker
from src.retrieval.query_expansion import expand_query
from src.generation.answer_generator import generate_answer
from src.generation.citation_guard import extract_citation_quotes, _normalize
from src.ingestion.sources import SOURCES
from pathlib import Path

ROOT = Path(".").resolve()
chunks = load_all_chunks(ROOT / "data" / "processed")
embedder = Embedder()
vector_store = VectorStore(persist_dir=ROOT / "data" / "vector_store")
bm25_index = BM25Index(chunks)
reranker = Reranker()
DOC_TITLES = {s.doc_id: s.title for s in SOURCES}

question = "Önlisans süresi ne kadardır?"
sub_queries = expand_query(question)
candidates_by_id = {}
guard_ids = []
for sq in sub_queries:
    for i, r in enumerate(hybrid_search(sq, embedder, vector_store, bm25_index, top_k=30)):
        cid = r["chunk_id"]
        if cid not in candidates_by_id or r["rrf_score"] > candidates_by_id[cid]["rrf_score"]:
            candidates_by_id[cid] = r
        if i < 5 and cid not in guard_ids:
            guard_ids.append(cid)
candidates = sorted(candidates_by_id.values(), key=lambda c: c["rrf_score"], reverse=True)
guard_pool = [candidates_by_id[cid] for cid in guard_ids]
top_chunks = reranker.rerank_with_safety_net(question, candidates, top_k=8, guard_pool=guard_pool)

answer = generate_answer(question, top_chunks, doc_titles=DOC_TITLES)
print("=== HAM CEVAP (tam) ===")
print(answer)
print("\n=== ALINTI KARSILASTIRMASI ===")
quotes = extract_citation_quotes(answer)
for num, quote in quotes.items():
    idx = num - 1
    if idx < len(top_chunks):
        source = top_chunks[idx]["text"]
        print(f"\n[{num}] Model alintisi: {quote!r}")
        print(f"[{num}] Kaynak metin   : {source[:200]!r}")
        print(f"[{num}] Normalize edilmis alinti: {_normalize(quote)[:100]!r}")
        print(f"[{num}] Normalize edilmis kaynak: {_normalize(source)[:100]!r}")
        print(f"[{num}] Eslesiyor mu: {_normalize(quote) in _normalize(source)}")
