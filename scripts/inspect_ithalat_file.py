import sys
sys.path.insert(0, ".")
from src.parsing.extractor import extract_text
from pathlib import Path

downloads = Path.home() / "Downloads"
files = sorted(downloads.glob("_PortalAdmin_Uploads_Content_FastAccess_*.doc*")) + \
        sorted(downloads.glob("_PortalAdmin_Uploads_Content_FastAccess_*.pdf"))

for f in files:
    try:
        text = extract_text(f).lower()
    except Exception:
        continue
    if "ithalat" in text and "uzlaştırma" in text:
        idx = text.find("ithalat")
        print(f.name[:20], "->", text[max(0,idx-20):idx+80])
