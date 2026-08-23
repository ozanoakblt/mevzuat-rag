"""
Kullanım:
    python scripts/search_full.py "sayaç arızası"

Tam retrieval pipeline'ı: Hybrid (Faz 6) ile top-20 aday çekilir, Reranker
(Faz 7) ile bunlar yeniden sıralanıp top-5'e indirilir. Reranker öncesi/
sonrası sıralamayı karşılaştırmalı gösterir — reranker'ın etkisini
görebilmeniz için.
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
CANDIDATE_POOL_SIZE = 20
FINAL_TOP_K = 5


def _print_results(results: list[dict], score_key: str) -> None:
    for i, r in enumerate(results, 1):
        loc = f"Madde {r['madde_no']}"
        if r.get("fikra_no"):
            loc += f", fıkra ({r['fikra_no']})"
        if r.get("bent_no"):
            loc += f", bent {r['bent_no']})"
        print(f"  [{i}] {r['doc_id']} — {loc}  ({score_key}: {r[score_key]:.4f})")
        if r.get("madde_baslik"):
            print(f"      Başlık: {r['madde_baslik']}")


def main() -> None:
    if len(sys.argv) < 2:
        print('Kullanım: python scripts/search_full.py "sorgu metni"')
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

    candidates = hybrid_search(
        query, embedder, vector_store, bm25_index, top_k=CANDIDATE_POOL_SIZE
    )

    print(f'\nSorgu: "{query}"\n{"=" * 60}')
    print(f"\n--- Reranker ÖNCESİ (Hybrid, ilk {FINAL_TOP_K}/{CANDIDATE_POOL_SIZE} aday) ---")
    _print_results(candidates[:FINAL_TOP_K], "rrf_score")

    print("\nReranker modeli yükleniyor (ilk seferde indirilecek, ~130 MB)...")
    reranker = Reranker()
    reranked = reranker.rerank_with_safety_net(query, candidates, top_k=FINAL_TOP_K)

    print(f"\n--- Reranker SONRASI (top {FINAL_TOP_K}) ---")
    _print_results(reranked, "rerank_score")

    before_ids = [r["chunk_id"] for r in candidates[:FINAL_TOP_K]]
    after_ids = [r["chunk_id"] for r in reranked]
    if before_ids == after_ids:
        print("\n(Sıralama değişmedi — hybrid zaten doğru sıradaydı.)")
    else:
        print("\n(Reranker sıralamayı değiştirdi.)")


if __name__ == "__main__":
    main()
