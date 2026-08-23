"""
Kullanım:
    python scripts/run_eval.py                    # sadece retrieval (hızlı, API çağrısı yok)
    python scripts/run_eval.py --with-generation   # + cevap üretimi ve faithfulness kontrolü (Groq gerekli, yavaş)

Brief madde 14: "Recall@K ve faithfulness gibi metrikleri bu küçük sette öl."

Recall@K: Beklenen (doc_id, madde) kombinasyonu, reranker'ın top-K
sonucunda var mı? "Kasıtlı zayıf kapsama" soruları (expected_documents
boş) için başarı ölçütü TERS ÇEVRİLİR: sistemin düşük güven göstermesi
(rerank skoru eşiğin altında) BAŞARI sayılır — çünkü doğru davranış
"bulamadım" demektir, bir şey bulmak değil.

Faithfulness (yalnızca --with-generation ile): üretilen cevaptaki
alıntıların gerçekten kaynakta olup olmadığı (citation_guard) — Faz 9'da
kurduğumuz doğrulama mekanizmasının aynısı.
"""
import argparse
import json
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
from src.generation.citation_guard import LOW_CONFIDENCE_RERANK_THRESHOLD, run_guard
from src.ingestion.sources import SOURCES
from src.retrieval.bm25_index import BM25Index
from src.retrieval.hybrid import hybrid_search
from src.retrieval.reranker import Reranker

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
VECTOR_STORE_DIR = ROOT / "data" / "vector_store"
EVAL_SET_PATH = ROOT / "eval" / "eval_set.json"
RESULTS_PATH = ROOT / "eval" / "results.json"

CANDIDATE_POOL_SIZE = 20
FINAL_TOP_K = 5
DOC_TITLES = {s.doc_id: s.title for s in SOURCES}


def _normalize_article(article: str) -> tuple[str, str]:
    """'MADDE 9' -> ('MADDE', '9'); 'EK MADDE 5' -> ('EK MADDE', '5')."""
    parts = article.rsplit(" ", 1)
    return parts[0], parts[1]


def _check_recall(reranked: list[dict], question: dict) -> bool:
    expected_docs = set(question["expected_documents"])
    expected_articles = {_normalize_article(a) for a in question["expected_articles"]}
    if not expected_docs:
        return None  # negatif test sorusu, recall@K uygulanmaz
    for chunk in reranked:
        if chunk["doc_id"] in expected_docs:
            if (chunk.get("madde_kind"), chunk.get("madde_no")) in expected_articles:
                return True
    return False


def run_single_question(
    question: dict, embedder, vector_store, bm25_index, reranker, with_generation: bool
) -> dict:
    candidates = hybrid_search(
        question["question"], embedder, vector_store, bm25_index, top_k=CANDIDATE_POOL_SIZE
    )
    reranked = reranker.rerank_with_safety_net(question["question"], candidates, top_k=FINAL_TOP_K)

    is_negative_test = not question["expected_documents"]
    best_score = max((c["rerank_score"] for c in reranked), default=None)

    result = {
        "id": question["id"],
        "difficulty": question["difficulty"],
        "is_negative_test": is_negative_test,
        "best_rerank_score": best_score,
    }

    if is_negative_test:
        # Başarı = düşük güven göstermek (sistem doğru şekilde "bulamadım" davranışında)
        result["correct_low_confidence"] = (
            best_score is not None and best_score < LOW_CONFIDENCE_RERANK_THRESHOLD
        )
    else:
        result["recall_hit"] = _check_recall(reranked, question)

    if with_generation:
        answer = generate_answer(question["question"], reranked, doc_titles=DOC_TITLES)
        guard = run_guard(answer, reranked)
        result["guard_low_confidence"] = guard.is_low_confidence
        result["ungrounded_citation_count"] = sum(
            1 for c in guard.citation_checks if not c.grounded
        )
        result["total_citation_count"] = len(guard.citation_checks)

    return result


def summarize(results: list[dict]) -> dict:
    positive = [r for r in results if not r["is_negative_test"]]
    negative = [r for r in results if r["is_negative_test"]]

    summary = {"total_questions": len(results)}

    if positive:
        hits = sum(1 for r in positive if r["recall_hit"])
        summary["recall_at_5_overall"] = hits / len(positive)
        for diff in ("kolay", "orta", "zor"):
            subset = [r for r in positive if r["difficulty"] == diff]
            if subset:
                sub_hits = sum(1 for r in subset if r["recall_hit"])
                summary[f"recall_at_5_{diff}"] = sub_hits / len(subset)

    if negative:
        correct = sum(1 for r in negative if r["correct_low_confidence"])
        summary["negative_test_success_rate"] = correct / len(negative)
        summary["negative_test_count"] = len(negative)

    if results and "total_citation_count" in results[0]:
        total_citations = sum(r["total_citation_count"] for r in results)
        ungrounded = sum(r["ungrounded_citation_count"] for r in results)
        summary["citation_groundedness_rate"] = (
            1.0 - (ungrounded / total_citations) if total_citations else None
        )

    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-generation", action="store_true")
    args = parser.parse_args()

    eval_data = json.loads(EVAL_SET_PATH.read_text(encoding="utf-8"))
    questions = eval_data["questions"]

    chunks = load_all_chunks(PROCESSED_DIR)
    if not chunks:
        print("data/processed/ içinde chunk bulunamadı. Önce scripts/parse.py çalıştırın.")
        sys.exit(1)

    print(f"{len(questions)} soru yükleniyor, bileşenler hazırlanıyor...")
    embedder = Embedder()
    vector_store = VectorStore(persist_dir=VECTOR_STORE_DIR)
    bm25_index = BM25Index(chunks)
    reranker = Reranker()

    if vector_store.count() == 0:
        print("Vektör index boş. Önce python scripts/build_index.py çalıştırın.")
        sys.exit(1)

    results = []
    for i, q in enumerate(questions, 1):
        print(f"  [{i}/{len(questions)}] {q['id']}: {q['question'][:60]}...")
        results.append(
            run_single_question(q, embedder, vector_store, bm25_index, reranker, args.with_generation)
        )

    summary = summarize(results)

    print(f"\n{'=' * 60}\nÖZET\n{'=' * 60}")
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2%}")
        else:
            print(f"  {key}: {value}")

    EVAL_SET_PATH.parent.mkdir(exist_ok=True)
    RESULTS_PATH.write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nDetaylı sonuçlar: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
