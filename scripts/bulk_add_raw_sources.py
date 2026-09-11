"""
data/raw'daki, henuz manifest.json'da kayitli olmayan tum PDF/DOC/DOCX
dosyalarini otomatik olarak manifest.json + src/ingestion/sources.py'ye
ekler. Filtreleme yapmaz.

Kullanim:
    python scripts/bulk_add_raw_sources.py            # onizleme
    python scripts/bulk_add_raw_sources.py --apply     # gercekten yaz
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.sources import SOURCES

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
MANIFEST_PATH = RAW_DIR / "manifest.json"
SOURCES_PATH = ROOT / "src" / "ingestion" / "sources.py"

SUPPORTED_SUFFIXES = {".pdf", ".doc", ".docx"}

_TR_MAP = str.maketrans({
    "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ı": "i", "I": "i",
    "İ": "i", "ö": "o", "Ö": "o", "ş": "s", "Ş": "s", "ü": "u", "Ü": "u",
})


def slugify(text: str) -> str:
    text = text.translate(_TR_MAP).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")[:80]


def clean_title(stem: str) -> str:
    stem = re.sub(r"^\d+_", "", stem)
    stem = stem.replace("_", " ")
    return re.sub(r"\s+", " ", stem).strip()


def guess_doc_type(filename: str) -> str:
    lower = filename.lower()
    checks = [
        ("kanun", "kanun"),
        ("yönetmelik", "yonetmelik"), ("yonetmelik", "yonetmelik"),
        ("tebliğ", "teblig"), ("teblig", "teblig"),
        ("yönerge", "yonerge"), ("yonerge", "yonerge"),
        ("usul", "usul-esas"),
        ("sözleşme", "anlasma-sozlesme"), ("sozlesme", "anlasma-sozlesme"),
        ("anlaşma", "anlasma-sozlesme"), ("anlasma", "anlasma-sozlesme"),
        ("protokol", "anlasma-sozlesme"),
        ("karar", "karar"),
        ("kılavuz", "kilavuz"), ("kilavuz", "kilavuz"),
        ("prosedür", "prosedur"), ("prosedur", "prosedur"),
    ]
    for keyword, doc_type in checks:
        if keyword in lower:
            return doc_type
    return "bilinmiyor"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    manifest = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    already_tracked_paths = {
        str(Path(entry["local_path"]).resolve())
        for entry in manifest.values()
        if entry.get("local_path")
    }
    existing_doc_ids = {s.doc_id for s in SOURCES} | set(manifest.keys())

    new_manifest_entries = {}
    new_source_lines = []
    skipped_unsupported = []
    used_doc_ids = set()

    for path in sorted(RAW_DIR.iterdir()):
        if not path.is_file() or path.name == "manifest.json":
            continue
        if str(path.resolve()) in already_tracked_paths:
            continue
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            skipped_unsupported.append(path.name)
            continue

        stem = path.stem
        base_doc_id = f"raw-{slugify(stem)}" or "raw-dosya"
        doc_id = base_doc_id
        suffix_n = 2
        while doc_id in existing_doc_ids or doc_id in used_doc_ids:
            doc_id = f"{base_doc_id}-{suffix_n}"
            suffix_n += 1
        used_doc_ids.add(doc_id)

        title = clean_title(stem)
        doc_type = guess_doc_type(path.name)
        sha = sha256_of(path)
        rel_path = f"data/raw/{path.name}"

        new_manifest_entries[doc_id] = {"local_path": rel_path, "sha256": sha}
        title_escaped = title.replace('"', '\\"')
        new_source_lines.append(
            f'    SourceDoc(\n'
            f'        doc_id="{doc_id}",\n'
            f'        title="{title_escaped}",\n'
            f'        url="",\n'
            f'        fetch_type="direct_file",\n'
            f'        doc_type="{doc_type}",\n'
            f'        notes="Elle toplu eklendi (bulk_add_raw_sources.py), orijinal dosya adi: {path.name}",\n'
            f'    ),'
        )

    print(f"Yeni eklenecek dosya sayisi: {len(new_manifest_entries)}")
    if skipped_unsupported:
        print(f"Desteklenmeyen uzanti nedeniyle atlanan ({len(skipped_unsupported)} dosya): {skipped_unsupported}")

    if not args.apply:
        print("\n--- ONIZLEME (henuz hicbir sey yazilmadi, --apply ile calistir) ---")
        for doc_id, entry in list(new_manifest_entries.items())[:10]:
            print(f"  {doc_id}  ->  {entry['local_path']}")
        if len(new_manifest_entries) > 10:
            print(f"  ... ve {len(new_manifest_entries) - 10} dosya daha")
        return

    manifest.update(new_manifest_entries)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    sources_text = SOURCES_PATH.read_text(encoding="utf-8")
    marker = "\n]\n\n\ndef direct_sources()"
    assert marker in sources_text, "sources.py'de beklenen SOURCES kapanis noktasi bulunamadi"
    insertion = "\n" + "\n".join(new_source_lines) + "\n]\n\n\ndef direct_sources()"
    sources_text = sources_text.replace(marker, insertion, 1)
    SOURCES_PATH.write_text(sources_text, encoding="utf-8")

    print(f"\nTAMAMLANDI: {len(new_manifest_entries)} yeni kaynak manifest.json ve sources.py'ye eklendi.")


if __name__ == "__main__":
    main()
