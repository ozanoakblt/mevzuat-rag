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

    all_embeddings = []
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["embedding_text"] for c in batch]
        embeddings = embedder.embed_passages(texts)
        all_embeddings.extend(embeddings)
        logger.info("  %d/%d embedding hesaplandi", min(i + BATCH_SIZE, len(chunks)), len(chunks))

    logger.info("Tum embedding'ler hesaplandi, Chroma'ya TEK seferde yaziliyor...")
    store.upsert_chunks(chunks, all_embeddings)
    logger.info("Tamamlandı. Toplam vektör sayısı: %d", store.count())

    # HNSW index'in arka planda tamamen diske yazilmasini (compaction)
    # bekleriz - bazi chromadb surumlerinde bu islem asenkron calisiyor ve
    # process hemen kapanirsa index dosyalari eksik/bozuk kalabiliyor.
    # Burada gercek bir sorgu calistirip sonra bekleyerek, index'in
    # process kapanmadan once diske yazilmasini garantiye almaya calisiyoruz.
    import time

    logger.info("Index'in diske tam yazilmasi icin dogrulama sorgusu calistiriliyor...")
    test_vec = embedder.embed_query("test sorgusu")
    for attempt in range(3):
        try:
            store.query(test_vec, n_results=1)
            logger.info("Dogrulama sorgusu basarili (deneme %d).", attempt + 1)
            break
        except Exception as exc:
            logger.warning("Dogrulama sorgusu basarisiz (deneme %d): %s", attempt + 1, exc)
            time.sleep(5)

    logger.info("Ek guvenlik bekleme suresi (10sn)...")
    time.sleep(10)
    logger.info("Bitti.")


if __name__ == "__main__":
    main()
