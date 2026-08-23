"""
Kullanım:
    python scripts/tag_scenarios.py

data/processed/*.json içindeki her madde için Groq'a kapalı-uçlu
sınıflandırma sorusu sorar, sonucu hem madde hem o maddeye ait tüm
chunk'lara yazar (chunk.scenario_tags), dosyayı günceller.

Gereksinim: .env dosyasında GROQ_API_KEY tanımlı olmalı
(https://console.groq.com/keys adresinden ücretsiz alınabilir).

MVP notu (brief madde 9): az doküman olduğu için sonuçlar elle gözden
geçirilebilir — bu script bittiğinde bir özet tablo basar, kontrol edin.
"""
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv kurulu değilse .env elle okunmuş olmalı (os.environ)

from src.tagging.scenario_tagger import classify_madde_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
REQUEST_DELAY_SECONDS = 2.0  # Groq ücretsiz kademe rate limit'ine karşı nazik ol


def tag_document(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    maddeler = data.get("maddeler", [])
    chunks = data.get("chunks", [])

    tags_by_madde: dict[str, list[str]] = {}
    for madde in maddeler:
        madde_no = madde["madde_no"]
        tags = classify_madde_text(madde["full_text"], madde.get("madde_baslik"))
        tags_by_madde[madde_no] = tags
        madde["scenario_tags"] = tags
        if tags:
            logger.info("[%s] madde %s -> %s", path.stem, madde_no, tags)
        time.sleep(REQUEST_DELAY_SECONDS)

    for chunk in chunks:
        chunk["scenario_tags"] = tags_by_madde.get(chunk["madde_no"], [])

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    files = sorted(PROCESSED_DIR.glob("*.json"))
    if not files:
        logger.error("data/processed/ içinde işlenecek dosya bulunamadı. Önce scripts/parse.py çalıştırın.")
        sys.exit(1)

    for f in files:
        logger.info("=== %s ===", f.name)
        tag_document(f)

    # Özet tablo (brief madde 9: "sonuçlar elle gözden geçirilebilir")
    logger.info("Tamamlandı. Özet:")
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        tagged = sum(1 for m in data.get("maddeler", []) if m.get("scenario_tags"))
        total = len(data.get("maddeler", []))
        logger.info("  %s: %d/%d madde en az 1 etiket aldı", f.stem, tagged, total)


if __name__ == "__main__":
    main()