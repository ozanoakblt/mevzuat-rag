"""
detect_duplicate_sources.py'nin buldugu HAM DOSYA tekrarlarini otomatik
temizler - kritik 7 grup HARIC (bunlara dokunulmaz).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "data" / "raw" / "manifest.json"
SOURCES_PATH = ROOT / "src" / "ingestion" / "sources.py"
PROCESSED_DIR = ROOT / "data" / "processed"

CRITICAL_GROUPS = [
    frozenset({"yonetmelik-baglanti-sistem-kullanim-2026-01-27", "usul-hat-katilim-bedeli"}),
    frozenset({"usul-dgp-etiket-smf", "usul-gop-teklif", "usul-kayip-katsayilari", "usul-profil-uygulamasi", "usul-karsiliksiz-islemler"}),
    frozenset({"usul-teminat-hesaplama-yontemi", "usul-teminat-esaslari"}),
    frozenset({"usul-tahmini-tuketim-degeri", "usul-fark-tutari"}),
    frozenset({"usul-akilli-sayac", "usul-osos"}),
    frozenset({"usul-onlisans-basvuru-belgeleri", "usul-tadil-devir-belgeleri"}),
    frozenset({"usul-teknik-kalite", "usul-cbs"}),
]


def is_critical(doc_ids):
    id_set = frozenset(doc_ids)
    return any(id_set >= crit for crit in CRITICAL_GROUPS)


def is_opaque(doc_id):
    if "portaladmin-uploads-content-fastaccess" in doc_id:
        return True
    if re.match(r"^raw-\d+-ind", doc_id):
        return True
    return False


def priority_key(doc_id):
    is_raw = doc_id.startswith("raw-")
    return (is_raw, is_opaque(doc_id), len(doc_id), doc_id)


def sha256_of_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def remove_source_doc_block(text, doc_id):
    pattern = re.compile(
        r'    SourceDoc\(\n'
        r'        doc_id="' + re.escape(doc_id) + r'",\n'
        r'.*?\n'
        r'    \),\n',
        re.DOTALL,
    )
    return pattern.subn("", text, count=1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    raw_hash_groups = defaultdict(list)
    for doc_id, entry in manifest.items():
        local_path = ROOT / entry["local_path"]
        if not local_path.exists():
            continue
        raw_hash_groups[sha256_of_file(local_path)].append(doc_id)

    dupe_groups = [ids for ids in raw_hash_groups.values() if len(ids) > 1]

    to_remove = []
    plan = []

    for ids in dupe_groups:
        if is_critical(ids):
            print(f"ATLANDI (kritik grup): {ids}")
            continue
        keeper = min(ids, key=priority_key)
        losers = [i for i in ids if i != keeper]
        plan.append((keeper, losers))
        to_remove.extend(losers)

    print(f"\nToplam {len(plan)} guvenli grup islenecek, {len(to_remove)} kayit kaldirilacak.\n")
    for keeper, losers in plan:
        print(f"  TUTULUYOR: {keeper}")
        for loser in losers:
            print(f"    kaldiriliyor: {loser}")

    if not args.apply:
        print("\n--- ONIZLEME - hicbir sey degistirilmedi. --apply ile calistir. ---")
        return

    for doc_id in to_remove:
        manifest.pop(doc_id, None)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    sources_text = SOURCES_PATH.read_text(encoding="utf-8")
    not_found = []
    for doc_id in to_remove:
        sources_text, count = remove_source_doc_block(sources_text, doc_id)
        if count == 0:
            not_found.append(doc_id)
    SOURCES_PATH.write_text(sources_text, encoding="utf-8")

    removed_processed = 0
    for doc_id in to_remove:
        processed_path = PROCESSED_DIR / f"{doc_id}.json"
        if processed_path.exists():
            processed_path.unlink()
            removed_processed += 1

    print(f"\nTAMAMLANDI: {len(to_remove)} kayit manifest.json'dan, sources.py'den kaldirildi.")
    print(f"{removed_processed} isli (data/processed) dosyasi silindi.")
    if not_found:
        print(f"UYARI: sources.py'de bulunamayan {len(not_found)} doc_id: {not_found}")


if __name__ == "__main__":
    main()
