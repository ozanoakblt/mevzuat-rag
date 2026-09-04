"""
Debug scripti: LLM/API katmani olmadan, dogrudan hybrid_search ve
reranker'i test eder. Bir sorgunun Madde 10/10-A gibi beklenen
maddeleri hangi asamada (retrieval mi, reranker mi) kaybettigini
gormek icin kullanilir.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.embedding.embedder import Embedder
from src.embedding.vector_store import VectorStore, load_all_chunks
from src.retrieval.bm25_index import BM25Index
from src.retrieval.hybrid import hybrid_search
from src.retrieval.reranker import Reranker

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
VECTOR_STORE_DIR = ROOT / "data" / "vector_store"

print("Bilesenler yukleniyor...")
chunks = load_all_chunks(PROCESSED_DIR)
embedder = Embedder()
vector_store = VectorStore(persist_dir=VECTOR_STORE_DIR)
bm25_index = BM25Index(chunks)
reranker = Reranker()

test_queries = [
    "Bağlantı ve sistem kullanım anlaşması nasıl yapılır?",
    "Bağlantı başvurusu nasıl yapılır?",
    "Bağlantı görüşü nedir?",
]

for q in test_queries:
    print(f"\n{'='*70}\nSORGU: {q}\n{'='*70}")

    candidates = hybrid_search(q, embedder, vector_store, bm25_index, top_k=30)
    print(f"\n-- Hybrid search top 30 (madde no'lar) --")
    for c in candidates:
        print(f"  Madde {c.get('madde_no')} {c.get('madde_kind')} (rrf={c['rrf_score']:.4f})")

    reranked = reranker.rerank_with_safety_net(q, candidates, top_k=8, guard_top_n=5)
    print(f"\n-- Reranker sonrasi final 8 --")
    for c in reranked:
        print(f"  Madde {c.get('madde_no')} {c.get('madde_kind')} (rerank={c['rerank_score']:.4f})")
