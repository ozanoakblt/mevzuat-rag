import sys
sys.path.insert(0, ".")
from src.parsing.extractor import extract_text
from pathlib import Path
import shutil
import re

def normalize(t):
    return re.sub(r"\s+", "", t.lower())

KEYWORDS = {
    "coğrafibilgisistem": "usul-cbs",
    "destekelemebedeli": "usul-destekleme-bedeli",  # yanlis yazim, asagida duzelttim
    "destekleme bedeli".replace(" ", ""): "usul-destekleme-bedeli",
    "etiketdeğerlerininbelirlenmesi": "usul-dgp-etiket-smf",
    "sistemmarjinalfiyatınınhesaplanması": "usul-dgp-etiket-smf",
    "farktutarı": "usul-fark-tutari",
    "ithalatveihracatailişkinuzlaştırma": "usul-ithalat-ihracat-uzlastirma",
    "karşılığıolmayanpiyasa": "usul-karsiliksiz-islemler",
    "kayıpkatsayı": "usul-kayip-katsayilari",
    "profiluygulamasınailişkin": "usul-profil-uygulamasi",
    "tadilbaşvurularıilebirleşme": "usul-tadil-devir-belgeleri",
    "tarifeuygulamalarınailişkin": "usul-tarife-uygulama",
    "toplamtüketimtahmini": "usul-toplam-tuketim-tahmini",
    "vadelielektrikpiyasası": "usul-vep",
}

already_done = {p.stem for p in Path("data/raw").glob("usul-*")} | {p.stem for p in Path("data/raw").glob("yonetmelik-*")}

downloads = Path.home() / "Downloads"
raw_dir = Path("data/raw")
files = sorted(downloads.glob("_PortalAdmin_Uploads_Content_FastAccess_*.doc*")) + \
        sorted(downloads.glob("_PortalAdmin_Uploads_Content_FastAccess_*.pdf"))

matched = {}

for f in files:
    try:
        text = normalize(extract_text(f))
    except Exception:
        continue
    for kw, doc_id in KEYWORDS.items():
        if doc_id in already_done or doc_id in matched:
            continue
        if kw in text:
            dest = raw_dir / f"{doc_id}{f.suffix.lower()}"
            shutil.copy(f, dest)
            matched[doc_id] = f.name
            break

print(f"YENI ESLESEN: {len(matched)}")
for doc_id in sorted(matched):
    print(" -", doc_id)

target_ids = {"usul-cbs", "usul-destekleme-bedeli", "usul-dgp-etiket-smf", "usul-fark-tutari",
              "usul-ithalat-ihracat-uzlastirma", "usul-karsiliksiz-islemler", "usul-kayip-katsayilari",
              "usul-profil-uygulamasi", "usul-tadil-devir-belgeleri", "usul-tarife-uygulama",
              "usul-toplam-tuketim-tahmini", "usul-vep"}
print(f"\nHALA BULUNAMAYAN: {sorted(target_ids - matched.keys())}")
