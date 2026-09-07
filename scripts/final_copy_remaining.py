import sys
sys.path.insert(0, ".")
from src.parsing.extractor import extract_text
from pathlib import Path
import shutil

KEYWORDS = {
    "ithalat ve ihracata ilişkin uzlaştırma": "usul-ithalat-ihracat-uzlastirma",
    "karşılığı olmayan": "usul-karsiliksiz-islemler",
    "kayıp katsayı": "usul-kayip-katsayilari",
    "profil uygulaması": "usul-profil-uygulamasi",
    "tarife uygulamaları": "usul-tarife-uygulama",
    "toplam tüketim": "usul-toplam-tuketim-tahmini",
}

downloads = Path.home() / "Downloads"
raw_dir = Path("data/raw")
files = sorted(downloads.glob("_PortalAdmin_Uploads_Content_FastAccess_*.doc*")) + \
        sorted(downloads.glob("_PortalAdmin_Uploads_Content_FastAccess_*.pdf"))

matched = {}
for f in files:
    try:
        text = extract_text(f).lower()
    except Exception:
        continue
    for kw, doc_id in KEYWORDS.items():
        if doc_id in matched:
            continue
        if kw in text:
            dest = raw_dir / f"{doc_id}{f.suffix.lower()}"
            shutil.copy(f, dest)
            matched[doc_id] = f.name

print(f"Kopyalanan: {len(matched)}/6")
for doc_id in sorted(matched):
    print(" -", doc_id)
missing = set(KEYWORDS.values()) - matched.keys()
if missing:
    print("Hala eksik:", sorted(missing))
