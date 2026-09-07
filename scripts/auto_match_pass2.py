import sys
sys.path.insert(0, ".")
from src.parsing.extractor import extract_text
from pathlib import Path
import shutil

KEYWORDS = {
    "önlisans başvurusunda sunulması gereken": "usul-onlisans-basvuru-belgeleri",
    "lisans başvurusunda sunulması gereken": "usul-lisans-basvuru-belgeleri",
    "tadil başvuruları ile birleşme": "usul-tadil-devir-belgeleri",
    "kaynak bazında destekleme bedelinin belirlenmesine": "usul-destekleme-bedeli",
    "akıllı sayaç sistemlerinin yaygınlaştırılmasına": "usul-akilli-sayac",
    "tarife uygulamalarına ilişkin usul": "usul-tarife-uygulama",
    "coğrafi bilgi sistemlerinin iyileştirilmesine": "usul-cbs",
    "hat katılım bedelinin belirlenmesine": "usul-hat-katilim-bedeli",
    "gün öncesi piyasası tekliflerinin yapısı": "usul-gop-teklif",
    "fark tutarı prosedürü": "usul-fark-tutari",
    "karşılığı olmayan piyasa işlemlerine": "usul-karsiliksiz-islemler",
    "ithalat ve ihracata ilişkin uzlaştırma": "usul-ithalat-ihracat-uzlastirma",
    "toplam tüketim tahmini belirleme": "usul-toplam-tuketim-tahmini",
    "tahmini tüketim değeri belirleme": "usul-tahmini-tuketim-degeri",
    "otomatik sayaç okuma sistemlerinin kapsamına": "usul-osos",
    "uzlaştırma hesaplamalarında kullanılacak profil": "usul-profil-uygulamasi",
    "vadeli elektrik piyasası işletim": "usul-vep",
    "kayıp katsayıları hesaplama metodolojisine": "usul-kayip-katsayilari",
    "sistem marjinal fiyatının hesaplanması": "usul-dgp-etiket-smf",
    "teminat hesaplama yöntemi": "usul-teminat-hesaplama-yontemi",
}

already_done = {"usul-fiyat-limitleri", "usul-santral-sahalari", "usul-talep-tarafi-sapma",
                 "usul-teknik-kalite", "usul-teminat-esaslari", "yonetmelik-seffaflik-piyasa-bozucu"}

downloads = Path.home() / "Downloads"
raw_dir = Path("data/raw")
files = sorted(downloads.glob("_PortalAdmin_Uploads_Content_FastAccess_*.doc*")) + \
        sorted(downloads.glob("_PortalAdmin_Uploads_Content_FastAccess_*.pdf"))

existing_raw = {p.stem for p in raw_dir.glob("usul-*")} | {p.stem for p in raw_dir.glob("yonetmelik-*")}

matched = {}
still_unmatched = 0

for f in files:
    try:
        text = extract_text(f).lower()
    except Exception:
        still_unmatched += 1
        continue
    found = None
    for kw, doc_id in KEYWORDS.items():
        if doc_id in already_done or doc_id in matched:
            continue
        if kw in text:
            found = doc_id
            break
    if found:
        dest = raw_dir / f"{found}{f.suffix.lower()}"
        shutil.copy(f, dest)
        matched[found] = f.name
    else:
        still_unmatched += 1

print(f"YENI ESLESEN: {len(matched)} dosya")
for doc_id in sorted(matched):
    print(" -", doc_id)
print(f"\nHALA ESLESMEYEN: {still_unmatched}")
print(f"\nBULUNAMAYAN (24 listeden): {sorted(set(KEYWORDS.values()) - matched.keys() - already_done)}")
