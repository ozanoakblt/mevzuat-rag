"""
Kullanım:
    python scripts/search.py "OSB bağlantı talebi hangi mevzuata tabi"

Sorguyu embed edip vektör index'te en yakın K sonucu basar. Bu, henüz bir
generation/citation katmanı değil — Faz 4'ün "sistem gerçekten arama
yapabiliyor mu" testidir. Faz 6'da BM25 ile birleşecek, Faz 8'de Groq
generation'a girdi olacak.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.embedding.embedder import Embedder
from src.embedding.vector_store import VectorStore

ROOT = Path(__file__).resolve().parent.parent
VECTOR_STORE_DIR = ROOT / "data" / "vector_store"


def main() -> None:
    if len(sys.argv) < 2:
        print('Kullanım: python scripts/search.py "sorgu metni"')
        sys.exit(1)
    query = " ".join(sys.argv[1:])

    embedder = Embedder()
    store = VectorStore(persist_dir=VECTOR_STORE_DIR)

    if store.count() == 0:
        print("Vektör index boş. Önce python scripts/build_index.py çalıştırın.")
        sys.exit(1)

    query_vec = embedder.embed_query(query)
    results = store.query(query_vec, n_results=5)

    print(f'\nSorgu: "{query}"\n{"=" * 60}')
    for i, r in enumerate(results, 1):
        m = r["metadata"]
        loc = f"Madde {m.get('madde_no')}"
        if m.get("fikra_no"):
            loc += f", fıkra ({m['fikra_no']})"
        if m.get("bent_no"):
            loc += f", bent {m['bent_no']})"
        print(f"\n[{i}] {m.get('doc_id')} — {loc}  (mesafe: {r['distance']:.4f})")
        if m.get("madde_baslik"):
            print(f"    Başlık: {m['madde_baslik']}")
        snippet = r["text"][:200].replace("\n", " ")
        print(f"    {snippet}...")


if __name__ == "__main__":
    main()
