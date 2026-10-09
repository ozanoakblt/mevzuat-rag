"""
Embedding modeli karsilastirmasi (alt-kume, sadece dense retrieval).

Tam indeksi (28 bin chunk) her aday model icin yeniden kurmak saatler surer.
Bunun yerine: eval sorularinin beklenen belgelerindeki TUM chunk'lar + sabit
tohumla secilmis rastgele "dikkat dagitici" chunk'lar uzerinde, her model icin
sadece dense (cosine) retrieval yapilir - BM25/reranker/query-expansion YOK,
yani fark dogrudan embedding kalitesinden gelir. Metrikler run_eval.py ile
ayni eslesme mantigini (_find_rank) kullanir. Sonuclar MLflow'a
("embedding-comparison") loglanir. Embedding'ler diske cache'lenir (devam
edilebilir).

Kullanim:
    python scripts/compare_embeddings.py intfloat/multilingual-e5-base BAAI/bge-m3
"""
import argparse
import importlib.util
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.embedding.vector_store import load_all_chunks  # noqa: E402

CACHE_DIR = ROOT / "data" / "embedding_compare_cache"
N_DISTRACTORS = 1500
MAX_SEQ_LENGTH = 512

# (query_prefix, passage_prefix)
PREFIXES = {
    "intfloat/multilingual-e5-base": ("query: ", "passage: "),
    "intfloat/multilingual-e5-large": ("query: ", "passage: "),
    "intfloat/multilingual-e5-small": ("query: ", "passage: "),
    "BAAI/bge-m3": ("", ""),
}


def _load_run_eval():
    spec = importlib.util.spec_from_file_location("run_eval", ROOT / "scripts" / "run_eval.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_subset(chunks, questions):
    expected_docs = {d for q in questions for d in q["expected_documents"]}
    inside = [c for c in chunks if c["doc_id"] in expected_docs]
    outside = [c for c in chunks if c["doc_id"] not in expected_docs]
    distractors = random.Random(0).sample(outside, min(N_DISTRACTORS, len(outside)))
    subset = inside + distractors
    subset.sort(key=lambda c: c["chunk_id"])  # deterministik sira
    return subset


def embed_passages(model_name, model, subset):
    safe = model_name.replace("/", "__")
    path = CACHE_DIR / f"{safe}__{len(subset)}.npy"
    if path.exists():
        return np.load(path)
    _, pp = PREFIXES.get(model_name, ("query: ", "passage: "))
    texts = [pp + (c.get("embedding_text") or c["text"]) for c in subset]
    t0 = time.time()
    vecs = model.encode(texts, batch_size=16, normalize_embeddings=True, show_progress_bar=False)
    print(f"  {len(texts)} chunk embed edildi: {time.time() - t0:.0f}s", flush=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    np.save(path, vecs)
    return vecs


def evaluate(model_name, run_eval, subset, questions):
    from sentence_transformers import SentenceTransformer

    print(f"[{model_name}] yukleniyor...", flush=True)
    model = SentenceTransformer(model_name)
    model.max_seq_length = MAX_SEQ_LENGTH
    passages = embed_passages(model_name, model, subset)

    qp, _ = PREFIXES.get(model_name, ("query: ", "passage: "))
    positive = [q for q in questions if q["expected_documents"]]
    qvecs = model.encode([qp + q["question"] for q in positive], normalize_embeddings=True, show_progress_bar=False)
    sims = qvecs @ passages.T

    results = []
    for i, q in enumerate(positive):
        order = np.argsort(-sims[i])[:10]
        ranked = [subset[j] for j in order]
        results.append({"recall_rank": run_eval._find_rank(ranked, q)})

    metrics = {}
    for k in (1, 3, 5, 10):
        metrics[f"recall_at_{k}"] = sum(1 for r in results if r["recall_rank"] and r["recall_rank"] <= k) / len(results)
    metrics["mrr"] = sum(1 / r["recall_rank"] for r in results if r["recall_rank"]) / len(results)
    return metrics


def log_mlflow(model_name, metrics, subset_size, n_questions):
    try:
        import mlflow

        mlflow.set_tracking_uri(f"sqlite:///{(ROOT / 'mlflow.db').as_posix()}")
        mlflow.set_experiment("embedding-comparison")
        with mlflow.start_run(run_name=model_name.split("/")[-1]):
            mlflow.log_params({
                "embedding_model": model_name,
                "subset_size": subset_size,
                "distractors": N_DISTRACTORS,
                "questions": n_questions,
                "max_seq_length": MAX_SEQ_LENGTH,
                "retrieval": "dense-only",
            })
            mlflow.log_metrics(metrics)
    except Exception as exc:  # noqa: BLE001
        print(f"MLflow loglama atlandi: {exc}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="+")
    args = parser.parse_args()

    run_eval = _load_run_eval()
    chunks = load_all_chunks(ROOT / "data" / "processed")
    questions = json.loads((ROOT / "eval" / "eval_set.json").read_text(encoding="utf-8"))["questions"]
    subset = build_subset(chunks, questions)
    n_pos = sum(1 for q in questions if q["expected_documents"])
    print(f"alt-kume: {len(subset)} chunk, {n_pos} pozitif soru", flush=True)

    for name in args.models:
        metrics = evaluate(name, run_eval, subset, questions)
        print(f"RESULT {name} " + json.dumps({k: round(v, 4) for k, v in metrics.items()}), flush=True)
        log_mlflow(name, metrics, len(subset), n_pos)


if __name__ == "__main__":
    main()
