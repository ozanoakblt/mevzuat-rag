"""
data/processed/'da artik olmayan (kaynak manifest.json'dan kaldirilmis)
belgelere ait, vektor index'te (data/vector_store) hala aranabilir kalan
"yetim" kayitlari temizler.

Neden gerekli: VectorStore.upsert_chunks() bir chunk'i GUNCELLERKEN eski
versiyonunu siler, ama bir KAYNAK data/processed'dan tamamen kaldirildiginda
(orn. duplicate temizligi) index'teki eski embeddingleri kimse silmiyor -
build_index.py'nin tam yeniden calistirilmasi (4-5 saat) disinda bir yol
yoktu. Gercek bir vakada tespit edildi: kaldirilmis bir kaynagin (raw-
elektrik-sebeke-yonetmeligi) 1400+ yetim chunk'i hala index'te aranabilir
durumdaydi ve guncel/dogru bir cevabin onune geciyordu (eval q20).

Kullanim:
    python scripts/prune_vector_orphans.py           # kac kayit silinecek, onizleme
    python scripts/prune_vector_orphans.py --apply    # gercekten sil

Ne zaman calistirilmali: data/raw/manifest.json ve data/processed/'dan bir
kaynak kaldirildiginda (orn. detect_duplicate_sources.py /
remove_bulk_duplicate_sources.py sonrasi), build_index.py'yi tam yeniden
calistirmadan once bu script'i calistirmak yeterlidir - sadece kaldirilan
kaynaklarin embeddinglerini siler, index'in geri kalanina dokunmaz.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.embedding.vector_store import VectorStore, load_all_chunks

PROCESSED_DIR = ROOT / "data" / "processed"
VECTOR_STORE_DIR = ROOT / "data" / "vector_store"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="gercekten sil (varsayilan: sadece onizle)")
    args = parser.parse_args()

    chunks = load_all_chunks(PROCESSED_DIR)
    valid_ids = {c["chunk_id"] for c in chunks}
    print(f"data/processed/'daki gecerli chunk sayisi: {len(valid_ids)}")

    store = VectorStore(persist_dir=VECTOR_STORE_DIR)
    before = store.count()
    print(f"Index'teki mevcut kayit sayisi: {before}")

    if not args.apply:
        orphan_count = sum(
            1 for cid in store._chunk_id_to_faiss_id if cid not in valid_ids
        )
        print(f"ONIZLEME: {orphan_count} yetim kayit bulundu (silmek icin --apply ekleyin).")
        return

    removed = store.prune_orphans(valid_ids)
    print(f"Silinen yetim kayit sayisi: {removed}")
    print(f"Index sonrasi kayit sayisi: {store.count()}")


if __name__ == "__main__":
    main()
