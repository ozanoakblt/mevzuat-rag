import sys
from pathlib import Path
sys.path.insert(0, str(Path(".").resolve()))

from src.ingestion.downloader import Downloader
from src.ingestion.sources import SOURCES

ROOT = Path(".").resolve()
downloader = Downloader(raw_dir=ROOT / "data" / "raw")

results = downloader.sync_raw_dir(SOURCES)

print(f"\n{len(results)} dosya islendi:")
for r in results:
    print(f"  [{r.status}] {r.doc_id} -> {r.local_path}")
