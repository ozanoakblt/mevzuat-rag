"""
Kullanım:
    python scripts/search_hybrid.py "sayaç arızası"

Faz 4 (dense) + Faz 5 (sparse/BM25) sonuçlarını RRF ile birleştirir.
Her sonucun hangi yöntem(ler)den geldiğini gösterir — [D]=dense, [S]=sparse,
[D+S]=her ikisinde de bulundu (en güçlü sinyal).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.embedding.embedder import Embedder
from src.embedding.vector_store import VectorStore, load_all_chunks
from src.retrieval.bm25_index import BM25Index
from src.retrieval.hybrid import hybrid_search

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
VECTOR_STORE_DIR = ROOT / "data" / "vector_store"


def main() -> None:
    if len(sys.argv) < 2:
        print('Kullanım: python scripts/search_hybrid.py "sorgu metni"')
        sys.exit(1)
    query = " ".join(sys.argv[1:])

    chunks = load_all_chunks(PROCESSED_DIR)
    if not chunks:
        print("data/processed/ içinde chunk bulunamadı. Önce scripts/parse.py çalıştırın.")
        sys.exit(1)

    embedder = Embedder()
    vector_store = VectorStore(persist_dir=VECTOR_STORE_DIR)
    bm25_index = BM25Index(chunks)

    if vector_store.count() == 0:
        print("Vektör index boş. Önce python scripts/build_index.py çalıştırın.")
        sys.exit(1)

    results = hybrid_search(query, embedder, vector_store, bm25_index, top_k=5)

    print(f'\nSorgu (Hybrid): "{query}"\n{"=" * 60}')
    for i, r in enumerate(results, 1):
        tag = "D+S" if r["in_dense"] and r["in_sparse"] else ("D" if r["in_dense"] else "S")
        loc = f"Madde {r['madde_no']}"
        if r.get("fikra_no"):
            loc += f", fıkra ({r['fikra_no']})"
        if r.get("bent_no"):
            loc += f", bent {r['bent_no']})"
        print(f"\n[{i}] [{tag}] {r['doc_id']} — {loc}  (RRF: {r['rrf_score']:.4f})")
        if r.get("madde_baslik"):
            print(f"    Başlık: {r['madde_baslik']}")
        snippet = r["text"][:200].replace("\n", " ")
        print(f"    {snippet}...")

    print(f"\n{'=' * 60}\n[D]=sadece embedding  [S]=sadece BM25  [D+S]=her ikisi de buldu (güçlü sinyal)")


if __name__ == "__main__":
    main()
