"""
Alternatif bir embedding modeliyle AYRI bir klasore indeks kurar - canli
indeksi (data/vector_store) ve mevcut modeli HICBIR zaman degistirmez.

Kesintiye dayaniklidir: her batch sonrasi diske yazilir, tekrar calistirilinca
zaten indekslenmis chunk'lari atlar (kaldigi yerden devam eder).

Kullanim:
    python scripts/build_index_alt.py --model BAAI/bge-m3 --out data/vector_store_bge_m3 --exclude-raw
    # sonra degerlendirme icin:
    EMBEDDING_MODEL=BAAI/bge-m3 VECTOR_STORE_DIR=data/vector_store_bge_m3 python scripts/run_eval.py

--exclude-raw: doc_id'si "raw-" ile baslayan toplu-import belgelerini atlar
(korpusun ~%57'si; aday modelin ilk, hizli degerlendirmesi icin).
"""
import argparse
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.embedding.embedder import Embedder  # noqa: E402
from src.embedding.vector_store import VectorStore, load_all_chunks  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = 16
SAVE_EVERY = 256  # chunk; her kayit tum indeksi diske yazar, cok sik yapma


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", required=True, help="indeks klasoru (canli indeksten FARKLI olmali)")
    parser.add_argument("--exclude-raw", action="store_true")
    args = parser.parse_args()

    out_dir = (ROOT / args.out).resolve()
    if out_dir == (ROOT / "data" / "vector_store").resolve():
        sys.exit("HATA: --out canli indeks klasoru olamaz.")

    chunks = load_all_chunks(ROOT / "data" / "processed")
    if args.exclude_raw:
        chunks = [c for c in chunks if not c["doc_id"].startswith("raw-")]

    store = VectorStore(persist_dir=out_dir)
    done = set(store._chunk_id_to_faiss_id.keys())
    todo = [c for c in chunks if c["chunk_id"] not in done]
    logger.info("model=%s | hedef=%d chunk | zaten var=%d | kalan=%d", args.model, len(chunks), len(done), len(todo))
    if not todo:
        logger.info("Yapilacak bir sey yok.")
        return

    embedder = Embedder(model_name=args.model)
    t0 = time.time()
    for start in range(0, len(todo), SAVE_EVERY):
        group = todo[start : start + SAVE_EVERY]
        embeddings = []
        for i in range(0, len(group), BATCH_SIZE):
            batch = group[i : i + BATCH_SIZE]
            embeddings.extend(embedder.embed_passages([c["embedding_text"] for c in batch]))
        store.upsert_chunks(group, embeddings)
        finished = start + len(group)
        rate = finished / (time.time() - t0)
        logger.info("%d/%d (%.1f chunk/sn, kalan ~%.0f dk)", finished, len(todo), rate, (len(todo) - finished) / rate / 60)
    logger.info("Bitti. Indeks: %s | toplam vektor: %d", out_dir, store.count())


if __name__ == "__main__":
    main()
