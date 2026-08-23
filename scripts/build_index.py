"""
Kullanım:
    python scripts/build_index.py

data/processed/*.json içindeki tüm chunk'ları okur, embedding'lerini
üretir (intfloat/multilingual-e5-base, ilk çalıştırmada ~1.1 GB indirir),
data/vector_store/ altına Chroma ile kalıcı olarak kaydeder.

İlk çalıştırma birkaç dakika sürebilir (model indirme + embedding).
Sonraki çalıştırmalarda model diskte önbelleklenmiş olur, sadece
embedding süresi kalır.
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.embedding.embedder import Embedder
from src.embedding.vector_store import VectorStore, load_all_chunks

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
VECTOR_STORE_DIR = ROOT / "data" / "vector_store"
BATCH_SIZE = 32


def main() -> None:
    chunks = load_all_chunks(PROCESSED_DIR)
    if not chunks:
        logger.error("data/processed/ içinde chunk bulunamadı. Önce scripts/parse.py çalıştırın.")
        sys.exit(1)
    logger.info("%d chunk bulundu, embedding üretiliyor (ilk seferde model indirilecek)...", len(chunks))

    embedder = Embedder()
    store = VectorStore(persist_dir=VECTOR_STORE_DIR)

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["embedding_text"] for c in batch]
        embeddings = embedder.embed_passages(texts)
        store.upsert_chunks(batch, embeddings)
        logger.info("  %d/%d chunk işlendi", min(i + BATCH_SIZE, len(chunks)), len(chunks))

    logger.info("Tamamlandı. Toplam vektör sayısı: %d", store.count())


if __name__ == "__main__":
    main()
