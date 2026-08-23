"""
Kullanım:
    python scripts/answer.py "OSB bağlantı talebi hangi mevzuata tabi"

Tam pipeline: Hybrid retrieval (top-20) -> Reranker (top-5) -> Groq ile
kaynak göstererek cevap üretimi. Bu, brief'in "senaryo bazlı sorulara
cevap verir" hedefinin ilk uçtan-uca çalışan hâli.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from src.embedding.embedder import Embedder
from src.embedding.vector_store import VectorStore, load_all_chunks
from src.generation.answer_generator import generate_answer
from src.generation.citation_guard import format_guard_warnings, run_guard
from src.ingestion.sources import SOURCES
from src.retrieval.bm25_index import BM25Index
from src.retrieval.hybrid import hybrid_search
from src.retrieval.reranker import Reranker

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
VECTOR_STORE_DIR = ROOT / "data" / "vector_store"
CANDIDATE_POOL_SIZE = 20
FINAL_TOP_K = 5

DOC_TITLES = {s.doc_id: s.title for s in SOURCES}


def main() -> None:
    if len(sys.argv) < 2:
        print('Kullanım: python scripts/answer.py "soru"')
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

    print("Kaynaklar aranıyor...")
    candidates = hybrid_search(
        query, embedder, vector_store, bm25_index, top_k=CANDIDATE_POOL_SIZE
    )

    print("Sonuçlar yeniden sıralanıyor (reranker)...")
    reranker = Reranker()
    top_chunks = reranker.rerank_with_safety_net(query, candidates, top_k=FINAL_TOP_K)

    print("Cevap üretiliyor (Groq)...\n")
    answer = generate_answer(query, top_chunks, doc_titles=DOC_TITLES)

    guard_result = run_guard(answer, top_chunks)
    warnings = format_guard_warnings(guard_result)

    print(f'Soru: "{query}"\n{"=" * 60}\n')
    if warnings:
        print(warnings)
        print()
    print(answer)

    print(f"\n{'=' * 60}\nKullanılan kaynaklar:")
    for i, c in enumerate(top_chunks, 1):
        title = DOC_TITLES.get(c["doc_id"], c["doc_id"])
        loc = f"Madde {c['madde_no']}"
        if c.get("fikra_no"):
            loc += f", fıkra ({c['fikra_no']})"
        print(f"  [{i}] {title} — {loc}  (rerank: {c['rerank_score']:.2f})")


if __name__ == "__main__":
    main()
