import sys
sys.path.insert(0, ".")
from src.parsing.extractor import extract_text
from pathlib import Path
import shutil

downloads = Path.home() / "Downloads"
raw_dir = Path("data/raw")
files = sorted(downloads.glob("_PortalAdmin_Uploads_Content_FastAccess_*.doc*")) + \
        sorted(downloads.glob("_PortalAdmin_Uploads_Content_FastAccess_*.pdf"))

for f in files:
    try:
        text = extract_text(f).lower()
    except Exception:
        continue
    if "ithalat ve ihracat faaliyetlerinde uygulanacak mali uzlaştırma" in text:
        dest = raw_dir / f"usul-ithalat-ihracat-uzlastirma{f.suffix.lower()}"
        shutil.copy(f, dest)
        print("Kopyalandi:", f.name, "->", dest.name)
        break
else:
    print("Bulunamadi.")
