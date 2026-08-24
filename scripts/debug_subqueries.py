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

ROOT = Path(".").resolve()
chunks = load_all_chunks(ROOT / "data" / "processed")
embedder = Embedder()
vector_store = VectorStore(persist_dir=ROOT / "data" / "vector_store")
bm25_index = BM25Index(chunks)

qs = expand_query("Bağlantı ve sistem kullanım anlaşması nasıl yapılır?")
for sq in qs:
    print("\n--- ALT-SORU:", sq)
    results = hybrid_search(sq, embedder, vector_store, bm25_index, top_k=5)
    for r in results:
        print("  Madde", r.get("madde_no"), r.get("madde_kind"))
