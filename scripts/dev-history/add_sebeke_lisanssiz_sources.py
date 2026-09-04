import pathlib

p = pathlib.Path("src/ingestion/sources.py")
text = p.read_text(encoding="utf-8")

anchor = "]\n\n\ndef direct_sources() -> list[SourceDoc]:"

new_entries = '''    SourceDoc(
        doc_id="yonetmelik-sebeke",
        title="Elektrik Sebeke Yonetmeligi",
        url="https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=&MevzuatTur=7&MevzuatTertip=5",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
        notes="Mevzuat.gov.tr uzerinden bulundu, elle indirildi (243 sayfa). Kesin Mevzuat No sonradan dogrulanip direct_file'a cevrilebilir.",
    ),
    SourceDoc(
        doc_id="yonetmelik-lisanssiz-uretim",
        title="Elektrik Piyasasinda Lisanssiz Elektrik Uretim Yonetmeligi",
        url="https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=&MevzuatTur=7&MevzuatTertip=5",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
        notes="Mevzuat.gov.tr uzerinden bulundu, elle indirildi (34 sayfa). Kesin Mevzuat No sonradan dogrulanip direct_file'a cevrilebilir.",
    ),
]


def direct_sources() -> list[SourceDoc]:'''

if anchor not in text:
    print("HATA: anchor bulunamadi.")
else:
    new_text = text.replace(anchor, new_entries)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili, 2 yeni kaynak eklendi.")
