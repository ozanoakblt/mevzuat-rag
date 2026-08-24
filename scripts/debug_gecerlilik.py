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

# Once: hedef chunk gercekten data icinde var mi, tam metnini gorelim
target = [c for c in chunks if c.get("madde_no") == "10/A" and c.get("fikra_no") == "4"]
print("--- Madde 10/A fikra 4 chunk'lari ---")
for c in target:
    print(" bent:", c.get("bent_no"), "| text:", c.get("text", "")[:120])

qs = expand_query("Bağlantı görüşü geçerlilik süresi kaç gün?")
for sq in qs:
    print(f"\n--- ALT-SORU: {sq}")
    results = hybrid_search(sq, embedder, vector_store, bm25_index, top_k=15)
    for r in results:
        marker = " <-- HEDEF" if r.get("madde_no") == "10/A" and r.get("fikra_no") == "4" and r.get("bent_no") == "a)" else ""
        print(f"  Madde {r.get('madde_no')} fikra {r.get('fikra_no')} bent {r.get('bent_no')} (rrf={r['rrf_score']:.4f}){marker}")
