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
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from src.embedding.embedder import DEFAULT_MODEL_NAME as DEFAULT_EMBEDDING_MODEL
from src.embedding.embedder import Embedder
from src.embedding.vector_store import VectorStore, load_all_chunks
from src.generation.answer_generator import generate_answer
from src.generation.citation_guard import LOW_CONFIDENCE_RERANK_THRESHOLD, run_guard
from src.ingestion.sources import SOURCES
from src.retrieval.bm25_index import BM25Index
from src.retrieval.pipeline import (
    CANDIDATE_POOL_SIZE,
    DOC_TYPE_BOOST_MULTIPLIER,
    FINAL_TOP_K,
    GUARD_ROUND_ROBIN_DEPTH,
    retrieve,
)
import os
import time

from src.retrieval.reranker import DEFAULT_RERANKER_MODEL, Reranker

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
VECTOR_STORE_DIR = Path(os.environ.get("VECTOR_STORE_DIR") or ROOT / "data" / "vector_store")
EVAL_SET_PATH = ROOT / "eval" / "eval_set.json"
RESULTS_PATH = ROOT / "eval" / "results.json"

DOC_TITLES = {s.doc_id: s.title for s in SOURCES}
# Eskiden run_eval.py'de doc-type boost (bkz. pipeline.py) UYGULANMIYORDU,
# sadece web/app.py'de vardi - yani eval sonuclari canli uygulamanin
# gercek davranisini yansitmiyordu (gercek bir drift vakasi, bkz.
# pipeline.py docstring'i). Artik ikisi de ayni retrieve() fonksiyonunu
# ayni DOC_TYPES haritasiyla cagiriyor.
DOC_TYPES = {s.doc_id: s.doc_type for s in SOURCES}
# Temporal/version-aware retrieval (bkz. src/retrieval/temporal.py) - ayni
# mantikla, run_eval.py'nin de web/app.py ile AYNI DOC_VERSIONS haritasini
# kullanmasi gerekir (aksi halde bu da yeni bir drift kaynagi olur).
DOC_VERSIONS = {
    s.doc_id: (s.version_group, date.fromisoformat(s.effective_from))
    for s in SOURCES
    if s.version_group and s.effective_from
}


def _normalize_article(article: str) -> tuple[str, str]:
    """'MADDE 9' -> ('MADDE', '9'); 'EK MADDE 5' -> ('EK MADDE', '5')."""
    parts = article.rsplit(" ", 1)
    return parts[0], parts[1]


def _article_matches(chunk: dict, expected_articles: set[tuple[str, str]]) -> bool:
    """
    expected_articles BOS ise (ama expected_documents DOLU) - soru belirli
    bir maddeye degil, TUM belgeye/konuya isaret ediyor demektir (orn.
    "teknik kaliteyi bozan unsurlar icin sureler nedir" gibi birden fazla
    fikraya yayilan sorular, ya da EPDK sinav testinden eklenen 36 soru -
    bunlarin cogu icin tek bir "dogru madde" belirlemek pratik degildi).
    Bu durumda MADDE eslesmesi ARANMAZ, sadece doc_id eslesmesi yeterlidir
    - aksi halde (eski davranis) bos kume hicbir (madde_kind, madde_no)
    ciftiyle ASLA eslesmez ve soru, retrieval ne kadar iyi olursa olsun
    HER ZAMAN "miss" sayilirdi (gercek bir vakada tespit edildi: 36 soru
    expected_articles=[] oldugu icin recall %10'a dusmus gorunuyordu -
    retrieval degil, olcum yontemi hataliydi).
    """
    if not expected_articles:
        return True
    return (chunk.get("madde_kind"), chunk.get("madde_no")) in expected_articles


def _check_recall(reranked: list[dict], question: dict) -> bool:
    expected_docs = set(question["expected_documents"])
    expected_articles = {_normalize_article(a) for a in question["expected_articles"]}
    if not expected_docs:
        return None  # negatif test sorusu, recall@K uygulanmaz
    for chunk in reranked:
        if chunk["doc_id"] in expected_docs and _article_matches(chunk, expected_articles):
            return True
    return False


def _find_rank(reranked: list[dict], question: dict) -> int | None:
    """Dogru maddenin reranked listesindeki 1-tabanli konumunu doner (MRR icin)."""
    expected_docs = set(question["expected_documents"])
    expected_articles = {_normalize_article(a) for a in question["expected_articles"]}
    if not expected_docs:
        return None
    for i, chunk in enumerate(reranked, 1):
        if chunk["doc_id"] in expected_docs and _article_matches(chunk, expected_articles):
            return i
    return None


def run_single_question(
    question: dict, embedder, vector_store, bm25_index, reranker, with_generation: bool
) -> dict:
    retrieval_start = time.perf_counter()
    q_text = question["question"]
    retrieval = retrieve(
        q_text, embedder, vector_store, bm25_index, reranker,
        doc_types=DOC_TYPES, doc_versions=DOC_VERSIONS,
    )
    reranked = retrieval.chunks
    retrieval_latency = time.perf_counter() - retrieval_start

    is_negative_test = not question["expected_documents"]
    best_score = max((c["rerank_score"] for c in reranked), default=None)

    result = {
        "id": question["id"],
        "difficulty": question["difficulty"],
        "is_negative_test": is_negative_test,
        "best_rerank_score": best_score,
        "retrieval_latency_seconds": round(retrieval_latency, 3),
    }

    if is_negative_test:
        # Başarı = düşük güven göstermek (sistem doğru şekilde "bulamadım" davranışında)
        result["correct_low_confidence"] = (
            best_score is not None and best_score < LOW_CONFIDENCE_RERANK_THRESHOLD
        )
    else:
        result["recall_hit"] = _check_recall(reranked, question)
        result["recall_rank"] = _find_rank(reranked, question)

    if with_generation:
        generation_start = time.perf_counter()
        answer, finish_reason = generate_answer(
            q_text, reranked, doc_titles=DOC_TITLES, return_finish_reason=True
        )
        result["generation_latency_seconds"] = round(time.perf_counter() - generation_start, 3)
        guard = run_guard(answer, reranked)
        result["guard_low_confidence"] = guard.is_low_confidence
        result["ungrounded_citation_count"] = sum(
            1 for c in guard.citation_checks if not c.grounded
        )
        result["total_citation_count"] = len(guard.citation_checks)
        result["finish_reason"] = finish_reason
        result["answer_text"] = answer

    return result


# Eskiden tek bir "recall_at_5_*" metrigi vardi ama K=5 ETIKETI YANLISTI -
# gercek retrieval derinligi FINAL_TOP_K=8'di (bkz. yukarida), yani
# raporlanan "recall@5" aslinda recall@8 olcuyordu. Bunun otesinde tek bir
# K, legal RAG icin yeterli sinyal vermiyor: "dogru madde bulundu mu"
# (kapsama) ile "dogru madde NE KADAR YUKARIDA" (siralama kalitesi) FARKLI
# sorular - orn. recall@8 %95.65 olsa bile MRR 0.495 gibi dusuk cikabilir,
# bu da sistemin cogu zaman dogru maddeyi buluyor ama onu ust siralara
# tasiyamadigini gosterir. recall_rank (1-tabanli pozisyon, _find_rank'ten)
# zaten her soru icin hesaplaniyor - K=1/3/5/8 kesitlerini buradan turetmek
# ekstra retrieval GEREKTIRMEZ, sadece "rank <= K mi" kontrolu.
_RECALL_K_VALUES = (1, 3, 5, FINAL_TOP_K)


def _recall_at_k(results: list[dict], k: int) -> float:
    hits = sum(1 for r in results if r.get("recall_rank") is not None and r["recall_rank"] <= k)
    return hits / len(results)


def _mrr_at_k(results: list[dict], k: int | None = None) -> float:
    reciprocal_ranks = [
        (1.0 / r["recall_rank"]) if r.get("recall_rank") and (k is None or r["recall_rank"] <= k) else 0.0
        for r in results
    ]
    return sum(reciprocal_ranks) / len(reciprocal_ranks)


def summarize(results: list[dict]) -> dict:
    positive = [r for r in results if not r["is_negative_test"]]
    negative = [r for r in results if r["is_negative_test"]]

    summary = {"total_questions": len(results)}

    if positive:
        for k in _RECALL_K_VALUES:
            summary[f"recall_at_{k}_overall"] = _recall_at_k(positive, k)
            for diff in ("kolay", "orta", "zor"):
                subset = [r for r in positive if r["difficulty"] == diff]
                if subset:
                    summary[f"recall_at_{k}_{diff}"] = _recall_at_k(subset, k)
        summary["mrr"] = _mrr_at_k(positive)
        summary["mrr_at_5"] = _mrr_at_k(positive, k=5)
        # Anahtar adi sabit "mrr_at_8" DEGIL, FINAL_TOP_K'ye gore dinamik -
        # aksi halde FINAL_TOP_K degisince (bkz. yukaridaki yorum: 8'den
        # 10'a cikarildi) tam bugunku "recall_at_5" yanlis adlandirma
        # hatasinin aynisini mrr icin tekrarlardik.
        summary[f"mrr_at_{FINAL_TOP_K}"] = _mrr_at_k(positive, k=FINAL_TOP_K)

    retrieval_latencies = [
        r["retrieval_latency_seconds"] for r in results if "retrieval_latency_seconds" in r
    ]
    if retrieval_latencies:
        summary["avg_retrieval_latency_seconds"] = round(
            sum(retrieval_latencies) / len(retrieval_latencies), 3
        )
    generation_latencies = [
        r["generation_latency_seconds"] for r in results if "generation_latency_seconds" in r
    ]
    if generation_latencies:
        summary["avg_generation_latency_seconds"] = round(
            sum(generation_latencies) / len(generation_latencies), 3
        )

    if negative:
        # --with-generation calistiysa gercek uretim davranisini (guard_low_confidence)
        # kullan; sadece retrieval skoruna (correct_low_confidence) bakmak yaniltici -
        # konuyla yuzeysel alakali ama cevabi olmayan sorularda retrieval skoru pozitif
        # cikabiliyor, oysa model dogru sekilde "bulamadim" diyebiliyor (bkz. q49/q51).
        def _negative_success(r: dict) -> bool:
            if "guard_low_confidence" in r:
                return r["guard_low_confidence"]
            return r["correct_low_confidence"]

        correct = sum(1 for r in negative if _negative_success(r))
        summary["negative_test_success_rate"] = correct / len(negative)
        summary["negative_test_count"] = len(negative)

    # results[0]'a bakmak yeterli degil: --ids ile kismi (bazen --with-generation'siz)
    # calistirmalar sonucunda results.json'da total_citation_count'u olan/olmayan
    # kayitlar bir arada bulunabilir - sadece bu alana sahip kayitlari say.
    with_citations = [r for r in results if "total_citation_count" in r]
    if with_citations:
        total_citations = sum(r["total_citation_count"] for r in with_citations)
        ungrounded = sum(r["ungrounded_citation_count"] for r in with_citations)
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


MLFLOW_EXPERIMENT_NAME = "legal-rag-retrieval"


def log_to_mlflow(summary: dict, with_generation: bool, question_count: int, run_name: str | None = None) -> None:
    """
    Eval kosusunu bir MLflow run'i olarak kaydeder - embedding/reranker
    modeli, RRF/guard/top-k parametreleri ve summarize()'in tum metrikleri
    (recall@1/3/5/{FINAL_TOP_K}, MRR, latency, citation groundedness vb.).
    Boylece farkli reranker/embedding modelleri ya da FINAL_TOP_K gibi
    parametre degisiklikleri ARASINDA (orn. "BGE reranker mi MiniLM mi
    daha iyi?") OLCULEBILIR bir karsilastirma yapilabilir - tek seferlik
    terminal ciktisina gomulup kaybolmak yerine.

    MLflow kurulu degilse ya da herhangi bir sebeple loglama basarisiz
    olursa (orn. mlruns/ dizinine yazma izni yok), eval SONUCUNU
    ETKILEMEZ - sadece bir uyari basilir ve devam edilir (projedeki diger
    "opsiyonel katman basarisiz olursa ana akisi kilitleme" felsefesiyle
    tutarli, bkz. applicability_checker.py/claim_verifier.py).
    """
    try:
        import mlflow
    except ImportError:
        print("UYARI: mlflow kurulu degil, deney takibi atlaniyor (pip install mlflow).")
        return

    try:
        # MLflow 3.x dosya-sistemi backend'ini (./mlruns) "bakim modu"na
        # aldi ve yeni ozellik almiyor - sqlite ise tek dosyali, sunucu
        # gerektirmeyen, MLflow'un kendi onerdigi zero-config alternatif
        # (bkz. https://mlflow.org/docs/latest/self-hosting/migrate-from-file-store).
        mlflow.set_tracking_uri(f"sqlite:///{(ROOT / 'mlflow.db').as_posix()}")
        mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
        with mlflow.start_run(run_name=run_name):
            mlflow.log_params({
                "embedding_model": os.environ.get("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
                "reranker_model": os.environ.get("RERANKER_MODEL", DEFAULT_RERANKER_MODEL),
                "candidate_pool_size": CANDIDATE_POOL_SIZE,
                "final_top_k": FINAL_TOP_K,
                "guard_round_robin_depth": GUARD_ROUND_ROBIN_DEPTH,
                "doc_type_boost_multiplier": DOC_TYPE_BOOST_MULTIPLIER,
                "with_generation": with_generation,
                "question_count": question_count,
            })
            mlflow.log_metrics({k: v for k, v in summary.items() if isinstance(v, (int, float))})
        print(f"MLflow run kaydedildi (deney: {MLFLOW_EXPERIMENT_NAME}).")
    except Exception as exc:  # pragma: no cover - sadece ortam sorunlarinda tetiklenir
        print(f"UYARI: MLflow loglama basarisiz oldu, eval sonucu etkilenmedi: {exc}")


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
    parser.add_argument(
        "--no-mlflow",
        action="store_true",
        help="MLflow deney takibine loglama yapma (varsayilan: loglanir).",
    )
    parser.add_argument(
        "--mlflow-run-name",
        type=str,
        default=None,
        help="MLflow run'ina verilecek isim (orn. 'bge-reranker-denemesi').",
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
            if "latency" in key:
                print(f"  {key}: {value:.3f}s")
            else:
                print(f"  {key}: {value:.2%}")
        else:
            print(f"  {key}: {value}")

    EVAL_SET_PATH.parent.mkdir(exist_ok=True)
    RESULTS_PATH.write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nDetaylı sonuçlar: {RESULTS_PATH}")

    if not args.no_mlflow:
        log_to_mlflow(
            summary, with_generation=args.with_generation,
            question_count=len(results), run_name=args.mlflow_run_name,
        )


if __name__ == "__main__":
    main()
