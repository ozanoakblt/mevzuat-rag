"""
manifest.json'daki tum kaynaklari tarar, birebir/duplikasyon tespiti
yapar - hicbir seyi SILMEZ, sadece raporlar.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.parsing.extractor import extract_text

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "data" / "raw" / "manifest.json"


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_text_for_hash(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", "", text)
    return text


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    raw_hash_groups = defaultdict(list)
    text_hash_groups = defaultdict(list)
    errors = []

    total = len(manifest)
    for i, (doc_id, entry) in enumerate(manifest.items(), 1):
        local_path = ROOT / entry["local_path"]
        if not local_path.exists():
            errors.append((doc_id, f"dosya bulunamadi: {local_path}"))
            continue

        try:
            raw_hash = sha256_of_file(local_path)
            raw_hash_groups[raw_hash].append(doc_id)
        except Exception as exc:
            errors.append((doc_id, f"hash hatasi: {exc}"))
            continue

        try:
            text = extract_text(str(local_path))
            norm = normalize_text_for_hash(text)
            if norm:
                text_hash = hashlib.sha256(norm.encode("utf-8")).hexdigest()
                text_hash_groups[text_hash].append(doc_id)
        except Exception as exc:
            errors.append((doc_id, f"metin cikarma hatasi: {exc}"))

        if i % 100 == 0:
            print(f"  ... {i}/{total} tarandi", file=sys.stderr)

    raw_dupes = {h: ids for h, ids in raw_hash_groups.items() if len(ids) > 1}
    text_dupes = {h: ids for h, ids in text_hash_groups.items() if len(ids) > 1}

    print(f"\n=== HAM DOSYA (byte-byte birebir) TEKRARLARI: {len(raw_dupes)} grup ===")
    for h, ids in raw_dupes.items():
        print(f"  {ids}")

    print(f"\n=== METIN ICERIGI (cikarilan metin birebir) TEKRARLARI: {len(text_dupes)} grup ===")
    for h, ids in text_dupes.items():
        if ids in raw_dupes.values():
            continue
        print(f"  {ids}")

    if errors:
        print(f"\n=== HATALAR: {len(errors)} dosya ===")
        for doc_id, err in errors[:20]:
            print(f"  {doc_id}: {err}")
        if len(errors) > 20:
            print(f"  ... ve {len(errors) - 20} hata daha")

    print(f"\nToplam: {total} kaynak tarandi.")


if __name__ == "__main__":
    main()
