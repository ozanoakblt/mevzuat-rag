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
from src.retrieval.query_expansion import expand_query
from src.retrieval.reranker import Reranker

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
VECTOR_STORE_DIR = ROOT / "data" / "vector_store"
EVAL_SET_PATH = ROOT / "eval" / "eval_set.json"
RESULTS_PATH = ROOT / "eval" / "results.json"

CANDIDATE_POOL_SIZE = 30
FINAL_TOP_K = 8
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
    q_text = question["question"]
    sub_queries = expand_query(q_text, embedder=embedder)
    candidates_by_id: dict[str, dict] = {}
    per_query_results: list[list[dict]] = []
    for sq in sub_queries:
        sq_results = hybrid_search(sq, embedder, vector_store, bm25_index, top_k=CANDIDATE_POOL_SIZE)
        per_query_results.append(sq_results)
        for r in sq_results:
            cid = r["chunk_id"]
            if cid not in candidates_by_id or r["rrf_score"] > candidates_by_id[cid]["rrf_score"]:
                candidates_by_id[cid] = r

    guard_ids: list[str] = []
    max_len = max((len(r) for r in per_query_results), default=0)
    for i in range(min(max_len, 13)):
        for sq_results in per_query_results:
            if i < len(sq_results):
                cid = sq_results[i]["chunk_id"]
                if cid not in guard_ids:
                    guard_ids.append(cid)
    candidates = sorted(candidates_by_id.values(), key=lambda c: c["rrf_score"], reverse=True)
    guard_pool = [candidates_by_id[cid] for cid in guard_ids]
    reranked = reranker.rerank_with_safety_net(
        q_text, candidates, top_k=FINAL_TOP_K, guard_pool=guard_pool
    )

    existing_ids = {c["chunk_id"] for c in reranked}
    ek_keys_selected = {
        (c["doc_id"], c["madde_no"]) for c in reranked if c.get("madde_kind") == "EK"
    }
    if ek_keys_selected:
        extra_ek_chunks = [
            c for c in candidates
            if c.get("madde_kind") == "EK"
            and (c["doc_id"], c["madde_no"]) in ek_keys_selected
            and c["chunk_id"] not in existing_ids
        ]
        if extra_ek_chunks:
            for c in extra_ek_chunks:
                c.setdefault("rerank_score", 0.0)
            reranked = reranked + extra_ek_chunks
            existing_ids.update(c["chunk_id"] for c in extra_ek_chunks)

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
        answer, finish_reason = generate_answer(
            q_text, reranked, doc_titles=DOC_TITLES, return_finish_reason=True
        )
        guard = run_guard(answer, reranked)
        result["guard_low_confidence"] = guard.is_low_confidence
        result["ungrounded_citation_count"] = sum(
            1 for c in guard.citation_checks if not c.grounded
        )
        result["total_citation_count"] = len(guard.citation_checks)
        result["finish_reason"] = finish_reason
        result["answer_text"] = answer

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


def select_sample(questions: list[dict], n: int) -> list[dict]:
    """
    Tam 49 soru yerine, gelistirme dongusunde hizli test icin N sorudan
    olusan dengeli bir alt kume secer. Negatif testlerden en az 1 tane
    (varsa) dahil edilir, kalani difficulty oranina gore bolusturulur.
    Secim deterministiktir - ayni N icin her zaman ayni sorular doner.
    """
    if n >= len(questions):
        return questions

    def stride_sample(items: list[dict], k: int) -> list[dict]:
        items = sorted(items, key=lambda q: q["id"])
        if k <= 0:
            return []
        if k >= len(items):
            return items
        step = len(items) / k
        indices = sorted({int(i * step) for i in range(k)})
        return [items[i] for i in indices]

    negatives = [q for q in questions if not q["expected_documents"]]
    positives_by_difficulty: dict[str, list[dict]] = {}
    for q in questions:
        if q["expected_documents"]:
            positives_by_difficulty.setdefault(q["difficulty"], []).append(q)

    n_negatives = 0
    if negatives:
        n_negatives = min(len(negatives), max(1, round(n * len(negatives) / len(questions))))
    n_remaining = n - n_negatives

    result = list(stride_sample(negatives, n_negatives))
    total_positive = sum(len(v) for v in positives_by_difficulty.values())
    allocated = 0
    diff_groups = sorted(positives_by_difficulty.items())
    for idx, (_difficulty, items) in enumerate(diff_groups):
        if idx == len(diff_groups) - 1:
            k = n_remaining - allocated
        elif total_positive:
            k = round(n_remaining * len(items) / total_positive)
        else:
            k = 0
        k = max(0, min(k, len(items)))
        result.extend(stride_sample(items, k))
        allocated += k

    return sorted(result, key=lambda q: q["id"])[:n]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-generation", action="store_true")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="eval/results.json'daki tamamlanmis sorulari atlayip devam et",
    )
    parser.add_argument(
        "--ids",
        type=str,
        default=None,
        help=(
            "virgulle ayrilmis soru id listesi (ornegin q02,q08,q49) - "
            "sadece bu sorulari, tamamlanmis olsalar bile ZORLA yeniden "
            "calistirir; results.json'daki diger tum kayitlari degistirmeden "
            "birakir. --resume ile birlikte kullanilirsa --ids kazanir."
        ),
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Tam sette degil, N sorudan olusan dengeli/deterministik bir alt kumede calistir.",
    )
    args = parser.parse_args()

    eval_data = json.loads(EVAL_SET_PATH.read_text(encoding="utf-8"))
    questions = eval_data["questions"]
    if args.sample is not None:
        questions = select_sample(questions, args.sample)
        print(f"Sample modu: {len(questions)} soru secildi ({[q['id'] for q in questions]}).")

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

    RESULTS_PATH.parent.mkdir(exist_ok=True)
    results = []
    completed_ids: set[str] = set()

    if args.ids:
        target_ids = {t.strip() for t in args.ids.split(",") if t.strip()}
        unknown = target_ids - {q["id"] for q in questions}
        if unknown:
            print(f"UYARI: eval_set.json'da olmayan id'ler: {sorted(unknown)}")
        if RESULTS_PATH.exists():
            prev = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
            results = [r for r in prev.get("results", []) if r["id"] not in target_ids]
        print(f"Hedefli calistirma: {len(target_ids)} soru ZORLA yeniden calisacak, digerleri korunuyor.")
        remaining = [q for q in questions if q["id"] in target_ids]
    elif args.resume and RESULTS_PATH.exists():
        prev = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
        prev_results = prev.get("results", [])
        completed_ids = {
            r["id"] for r in prev_results
            if (not args.with_generation) or ("total_citation_count" in r)
        }
        results = [r for r in prev_results if r["id"] in completed_ids]
        print(f"Resume: {len(completed_ids)}/{len(questions)} soru daha once tamamlanmis, atlaniyor.")
        remaining = [q for q in questions if q["id"] not in completed_ids]
    else:
        remaining = questions
    for i, q in enumerate(remaining, 1):
        print(f"  [{i}/{len(remaining)}] {q['id']}: {q['question'][:60]}...")
        results.append(
            run_single_question(q, embedder, vector_store, bm25_index, reranker, args.with_generation)
        )
        # Checkpoint: her soru sonrasi ara sonucu diske yaz - uzun
        # calisan (--with-generation) modda rate-limit gibi bir kesinti
        # olursa, o ana kadarki sonuclar kaybolmasin (gercek bir vakada
        # 49 sorudan 24'u basariyla tamamlanmisken Groq 429 hatasi
        # verdi ve tum 24 sonuc bellekte kalip diske hic yazilamadi).
        partial_summary = summarize(results)
        RESULTS_PATH.write_text(
            json.dumps(
                {"summary": partial_summary, "results": results, "completed": len(results), "total": len(questions)},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
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
