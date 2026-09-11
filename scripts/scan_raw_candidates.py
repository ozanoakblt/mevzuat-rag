"""
data/raw'daki TUM dosyalari tarar, her birinden ne kadar metin cikarilabildigini
(karakter sayisi) olcer ve KISADAN UZUNA siralar.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.parsing.extractor import extract_text

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
MANIFEST_PATH = RAW_DIR / "manifest.json"

SUPPORTED_SUFFIXES = {".pdf", ".doc", ".docx"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-chars", type=int, default=500)
    args = parser.parse_args()

    manifest = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    already_tracked_paths = {
        str(Path(entry["local_path"]).resolve())
        for entry in manifest.values()
        if entry.get("local_path")
    }

    candidates = []
    skipped_extension = []
    skipped_tracked = 0

    for path in sorted(RAW_DIR.iterdir()):
        if not path.is_file():
            continue
        if path.name == "manifest.json":
            continue
        if str(path.resolve()) in already_tracked_paths:
            skipped_tracked += 1
            continue
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            skipped_extension.append(path.name)
            continue

        try:
            text = extract_text(str(path))
            char_count = len(text.strip())
            candidates.append((char_count, path.name, ""))
        except Exception as exc:
            candidates.append((-1, path.name, str(exc)[:80]))

    candidates.sort(key=lambda c: c[0])

    print(f"Toplam aday dosya: {len(candidates)} (mevcut manifest'te olan {skipped_tracked} dosya atlandi)\n")

    if skipped_extension:
        print(f"Desteklenmeyen uzanti ({len(skipped_extension)} dosya, atlandi): {skipped_extension[:10]}")

    print(f"{'KARAKTER':>10}  DOSYA")
    print("-" * 70)
    for char_count, name, error in candidates:
        if error:
            print(f"{'HATA':>10}  {name}  ({error})")
        elif char_count < args.min_chars:
            print(f"{char_count:>10}  {name}  <-- SUPHELI (KISA)")
        else:
            print(f"{char_count:>10}  {name}")

    short_count = sum(1 for c, _, e in candidates if not e and c < args.min_chars)
    print(f"\n{short_count} dosya {args.min_chars} karakterin altinda - muhtemelen ekipman/tekil kayit, mevzuat degil.")


if __name__ == "__main__":
    main()
