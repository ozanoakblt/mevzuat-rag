"""
Kullanım:
    python scripts/search_bm25.py "sayaç arızası"

Faz 4'teki search.py'nin BM25 (anahtar kelime) karşılığı. İkisini
karşılaştırarak dense/sparse aramanın nerede farklı sonuç verdiğini
görebilirsiniz — Faz 6'da bu ikisi birleştirilecek.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.embedding.vector_store import load_all_chunks
from src.retrieval.bm25_index import BM25Index

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"


def main() -> None:
    if len(sys.argv) < 2:
        print('Kullanım: python scripts/search_bm25.py "sorgu metni"')
        sys.exit(1)
    query = " ".join(sys.argv[1:])

    chunks = load_all_chunks(PROCESSED_DIR)
    if not chunks:
        print("data/processed/ içinde chunk bulunamadı. Önce scripts/parse.py çalıştırın.")
        sys.exit(1)

    index = BM25Index(chunks)
    results = index.search(query, top_k=5)

    print(f'\nSorgu (BM25): "{query}"\n{"=" * 60}')
    if not results:
        print("Hiç eşleşme bulunamadı (anahtar kelime araması, embedding'den farklı olarak).")
        return

    for i, r in enumerate(results, 1):
        loc = f"Madde {r['madde_no']}"
        if r.get("fikra_no"):
            loc += f", fıkra ({r['fikra_no']})"
        if r.get("bent_no"):
            loc += f", bent {r['bent_no']})"
        print(f"\n[{i}] {r['doc_id']} — {loc}  (BM25 skoru: {r['bm25_score']:.4f})")
        if r.get("madde_baslik"):
            print(f"    Başlık: {r['madde_baslik']}")
        snippet = r["text"][:200].replace("\n", " ")
        print(f"    {snippet}...")


if __name__ == "__main__":
    main()
