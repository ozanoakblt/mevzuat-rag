import sys
sys.path.insert(0, ".")
from src.parsing.extractor import extract_text
from pathlib import Path

already_matched_files = set()
import shutil
raw_dir = Path("data/raw")
# Zaten eslesen dosyalarin orijinal isimlerini tekrar okumaya calismayalim,
# bunun yerine downloads'daki TUM dosyalari tarayip, henuz data/raw'a
# KOPYALANMAMIS olanlari (yani boyutu farkli/yeni olanlari) listeleyelim.
# Basitce: her dosyanin ilk satirini yazdiralim, gozle bulalim.

downloads = Path.home() / "Downloads"
files = sorted(downloads.glob("_PortalAdmin_Uploads_Content_FastAccess_*.doc*")) + \
        sorted(downloads.glob("_PortalAdmin_Uploads_Content_FastAccess_*.pdf"))

target_words = ["ithalat", "karşılığı olmayan", "kayıp katsayı", "profil uygulaması", "tarife uygulamaları", "toplam tüketim"]

for f in files:
    try:
        text = extract_text(f).lower()
    except Exception:
        continue
    for w in target_words:
        if w in text:
            print(f.name[:20], "->", w)
