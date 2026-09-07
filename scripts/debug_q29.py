import sys
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

from src.embedding.embedder import Embedder
from src.embedding.vector_store import VectorStore, load_all_chunks
from src.retrieval.bm25_index import BM25Index
from src.retrieval.hybrid import hybrid_search
from src.retrieval.query_expansion import expand_query
from pathlib import Path

ROOT = Path(".").resolve()
chunks = load_all_chunks(ROOT / "data" / "processed")
embedder = Embedder()
vector_store = VectorStore(persist_dir=ROOT / "data" / "vector_store")
bm25_index = BM25Index(chunks)

def is_target(r):
    return r.get("doc_id") == "kanun-6446" and r.get("madde_no") == "17"

question = "Teknik olmayan kayıp (kaçak kullanım) maliyetleri tarifelere nasıl yansıtılır?"
sub_queries = expand_query(question)
for sq in sub_queries:
    print(f"--- {sq}")
    results = hybrid_search(sq, embedder, vector_store, bm25_index, top_k=30)
    found = next((i for i, r in enumerate(results) if is_target(r)), None)
    print(f"  Madde 17 top-30'da: {found}")
