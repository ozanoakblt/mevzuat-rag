"""
data/processed/'daki chunk'lar ile data/vector_store'daki mevcut index
arasindaki farki bulur ve SADECE eksik/yeni olanlari embedleyip ekler -
build_index.py'nin tersine (tum korpusu sifirdan embedler, 4-5 saat),
bu script sadece degisen kismi isler (tipik olarak birkac yuz-bin chunk,
birkac dakika).

Kullanim:
    python scripts/sync_vector_index.py            # onizleme
    python scripts/sync_vector_index.py --apply     # gercekten embed+ekle

Ne zaman calistirilmali: data/processed/ icerigi degistiginde (yeni kaynak
eklendiginde, ya da scripts/parse.py bir duzeltmeyle yeniden calistirildiginda,
orn. structure_parser.py'deki bir regex duzeltmesi sonrasi).
"""
import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.embedding.embedder import Embedder
from src.embedding.vector_store import VectorStore, load_all_chunks

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROCESSED_DIR = ROOT / "data" / "processed"
VECTOR_STORE_DIR = ROOT / "data" / "vector_store"
BATCH_SIZE = 32


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="gercekten embed+ekle (varsayilan: sadece onizle)")
    args = parser.parse_args()

    chunks = load_all_chunks(PROCESSED_DIR)
    current_ids = {c["chunk_id"] for c in chunks}
    logger.info("data/processed'daki toplam chunk: %d", len(chunks))

    store = VectorStore(persist_dir=VECTOR_STORE_DIR)
    indexed_ids = set(store._chunk_id_to_faiss_id.keys())
    logger.info("Index'teki mevcut kayit: %d", store.count())

    new_ids = current_ids - indexed_ids
    logger.info("Eksik/yeni chunk sayisi (embed edilecek): %d", len(new_ids))

    if not new_ids:
        logger.info("Senkron - yapilacak bir sey yok.")
        return
    if not args.apply:
        logger.info("ONIZLEME modu - gercekten eklemek icin --apply ekleyin.")
        return

    new_chunks = [c for c in chunks if c["chunk_id"] in new_ids]
    embedder = Embedder()
    all_embeddings = []
    for i in range(0, len(new_chunks), BATCH_SIZE):
        batch = new_chunks[i : i + BATCH_SIZE]
        texts = [c["embedding_text"] for c in batch]
        embeddings = embedder.embed_passages(texts)
        all_embeddings.extend(embeddings)
        logger.info("  %d/%d embedding hesaplandi", min(i + BATCH_SIZE, len(new_chunks)), len(new_chunks))

    store.upsert_chunks(new_chunks, all_embeddings)
    logger.info("Tamamlandi. Index'teki toplam kayit: %d", store.count())


if __name__ == "__main__":
    main()
