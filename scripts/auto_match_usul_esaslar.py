import sys
sys.path.insert(0, ".")
from src.parsing.extractor import extract_text
from pathlib import Path
import shutil

KEYWORDS = {
    "santral sahalarının belirlenmesine": "usul-santral-sahalari",
    "önlisans başvurusunda sunulması gereken": "usul-onlisans-basvuru-belgeleri",
    "lisans başvurusunda sunulması gereken": "usul-lisans-basvuru-belgeleri",
    "tadil başvuruları ile birleşme": "usul-tadil-devir-belgeleri",
    "teminat usul ve esaslar": "usul-teminat-esaslari",
    "kaynak bazında destekleme bedelinin belirlenmesine": "usul-destekleme-bedeli",
    "talep tarafı katılımı hizmeti kapsamında": "usul-talep-tarafi-sapma",
    "akıllı sayaç sistemlerinin yaygınlaştırılmasına": "usul-akilli-sayac",
    "tarife uygulamalarına ilişkin usul": "usul-tarife-uygulama",
    "dağıtım sisteminin teknik kalitesine": "usul-teknik-kalite",
    "coğrafi bilgi sistemlerinin iyileştirilmesine": "usul-cbs",
    "hat katılım bedelinin belirlenmesine": "usul-hat-katilim-bedeli",
    "gün öncesi piyasası tekliflerinin yapısı": "usul-gop-teklif",
    "asgari ve azami fiyat limitlerinin belirlenmesine": "usul-fiyat-limitleri",
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
    "şeffaflığa ve piyasa bozucu davranışlara": "yonetmelik-seffaflik-piyasa-bozucu",
}

downloads = Path.home() / "Downloads"
raw_dir = Path("data/raw")
files = sorted(downloads.glob("_PortalAdmin_Uploads_Content_FastAccess_*.doc*")) + \
        sorted(downloads.glob("_PortalAdmin_Uploads_Content_FastAccess_*.pdf"))

matched = {}
unmatched = []

for f in files:
    try:
        text = extract_text(f).lower()
    except Exception:
        unmatched.append(f.name)
        continue
    snippet = text[:1500]
    found = None
    for kw, doc_id in KEYWORDS.items():
        if kw in snippet:
            found = doc_id
            break
    if found:
        dest = raw_dir / f"{found}{f.suffix.lower()}"
        shutil.copy(f, dest)
        matched[found] = f.name
    else:
        unmatched.append(f.name)

print(f"ESLESEN: {len(matched)} dosya")
for doc_id in sorted(matched):
    print(" -", doc_id)
print(f"\nESLESMEYEN: {len(unmatched)} dosya (bunlar muhtemelen zaten eklediklerimiz - ana yonetmelikler)")
