"""
Kullanım:
    python scripts/parse.py

data/raw/manifest.json'daki her kayıtlı belgeyi okur, sources.py'den
title/doc_type/completeness_note bilgisini eşler, ayrıştırıp
data/processed/<doc_id>.json olarak yazar.
"""
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.sources import SOURCES
from src.parsing.extractor import extract_text
from src.parsing.metadata import DocumentMetadata, parse_and_save

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
MANIFEST_PATH = RAW_DIR / "manifest.json"

SOURCES_BY_ID = {s.doc_id: s for s in SOURCES}

# Bağlantı Yönetmeliği'nin iki parçası birbirine referans versin (bkz. sources.py notu).
RELATED_DOCUMENTS = {
    "yonetmelik-baglanti-sistem-kullanim-2026-01-27": [
        "yonetmelik-baglanti-sistem-kullanim-2026-06-25-degisiklik"
    ],
    "yonetmelik-baglanti-sistem-kullanim-2026-06-25-degisiklik": [
        "yonetmelik-baglanti-sistem-kullanim-2026-01-27"
    ],
}


def main() -> None:
    if not MANIFEST_PATH.exists():
        logger.error("manifest.json bulunamadı — önce scripts/ingest.py çalıştırın.")
        sys.exit(1)

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    for doc_id, entry in manifest.items():
        local_path = entry.get("local_path")
        if not local_path or not Path(local_path).exists():
            logger.warning("[%s] dosya bulunamadı (%s), atlanıyor.", doc_id, local_path)
            continue

        source = SOURCES_BY_ID.get(doc_id)
        title = source.title if source else doc_id
        doc_type = source.doc_type if source else "bilinmiyor"
        completeness_note = source.completeness_note if source else ""

        logger.info("[%s] ayrıştırılıyor: %s", doc_id, local_path)
        try:
            raw_text = extract_text(local_path)
        except Exception:
            logger.exception("[%s] metin çıkarma başarısız", doc_id)
            continue

        doc_meta = DocumentMetadata(
            doc_id=doc_id,
            title=title,
            doc_type=doc_type,
            source_local_path=local_path,
            sha256=entry.get("sha256", ""),
            completeness_note=completeness_note,
            related_documents=RELATED_DOCUMENTS.get(doc_id, []),
        )

        out_path = parse_and_save(doc_meta, raw_text, PROCESSED_DIR)
        logger.info("[%s] yazıldı -> %s", doc_id, out_path)

    logger.info("Tamamlandı. Çıktılar: %s", PROCESSED_DIR)


if __name__ == "__main__":
    main()
