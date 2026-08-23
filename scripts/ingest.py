"""
Kullanım:
    python scripts/ingest.py
        Madde 5'teki sabit URL listesindeki "direct_file" tipli kaynakları
        indirir. robots.txt bir kaynağı engelliyorsa otomatik indirme
        DURDURULUR ve o kaynak için elle-indirme talimatı basılır.

    python scripts/ingest.py --register-manual <doc_id> <dosya_yolu>
        robots.txt tarafından engellenen (veya needs_resolution) bir belgeyi
        tarayıcınızdan elle indirdikten sonra bu komutla sisteme kaydedin.
        Örnek:
        python scripts/ingest.py --register-manual kanun-6446 ~/Downloads/6446.pdf

    python scripts/ingest.py --sync
        data/raw/ klasörüne doc_id.<uzantı> formatında elle koyduğunuz TÜM
        dosyaları tek seferde tarar, hash'ler ve manifest'e kaydeder.
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.downloader import Downloader
from src.ingestion.sources import SOURCES, direct_sources, needs_resolution_sources

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def register_manual(doc_id: str, file_path: str) -> None:
    source = next((s for s in SOURCES if s.doc_id == doc_id), None)
    if source is None:
        logger.error("Bilinmeyen doc_id: %s (sources.py içindeki listeye bakın)", doc_id)
        sys.exit(1)
    downloader = Downloader(raw_dir=RAW_DIR)
    result = downloader.register_manual_file(source, file_path)
    logger.info("[%s] kaydedildi: %s", result.doc_id, result.status)


def sync_raw() -> None:
    downloader = Downloader(raw_dir=RAW_DIR)
    results = downloader.sync_raw_dir(SOURCES)
    if not results:
        logger.warning("data/raw/ içinde beklenen isimde hiçbir dosya bulunamadı.")
        return
    logger.info("Senkronizasyon özeti:")
    for r in results:
        logger.info("  [%s] %s", r.doc_id, r.status)


def main() -> None:
    downloader = Downloader(raw_dir=RAW_DIR)

    pending = needs_resolution_sources()
    if pending:
        logger.warning(
            "%d kaynak elle çözümleme bekliyor (otomatik indirilmedi):", len(pending)
        )
        for s in pending:
            logger.warning("  - [%s] %s -> %s", s.doc_id, s.title, s.url)

    results = []
    for source in direct_sources():
        try:
            result = downloader.fetch(source)
            results.append(result)
            if result.status == "skipped_robots_disallowed":
                logger.warning(
                    "[%s] robots.txt engelledi. Elle indirin ve şu komutla kaydedin:\n"
                    "    python scripts/ingest.py --register-manual %s <indirilen_dosya_yolu>",
                    source.doc_id,
                    source.doc_id,
                )
        except Exception:
            logger.exception("[%s] indirme başarısız", source.doc_id)

    logger.info("Özet:")
    for r in results:
        logger.info("  [%s] %s", r.doc_id, r.status)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--register-manual":
        if len(sys.argv) != 4:
            print("Kullanım: python scripts/ingest.py --register-manual <doc_id> <dosya_yolu>")
            sys.exit(1)
        register_manual(sys.argv[2], sys.argv[3])
    elif len(sys.argv) > 1 and sys.argv[1] == "--sync":
        sync_raw()
    else:
        main()