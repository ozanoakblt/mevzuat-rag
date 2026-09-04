import pathlib

p = pathlib.Path("src/ingestion/sources.py")
text = p.read_text(encoding="utf-8")

anchor = "]\n\n\ndef direct_sources() -> list[SourceDoc]:"

new_entries = '''    SourceDoc(
        doc_id="kanun-5346",
        title="5346 Sayili Yenilenebilir Enerji Kaynaklarinin Elektrik Enerjisi Uretimi Amacli Kullanimina Iliskin Kanun",
        url="",
        fetch_type="needs_resolution",
        doc_type="kanun",
        notes="Mevzuat.gov.tr uzerinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="kanun-4628",
        title="4628 Sayili Enerji Piyasasi Duzenleme Kurumunun Teskilat ve Gorevleri Hakkinda Kanun",
        url="",
        fetch_type="needs_resolution",
        doc_type="kanun",
        notes="Mevzuat.gov.tr uzerinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="yonetmelik-ithalat-ihracat",
        title="Elektrik Piyasasi Ithalat ve Ihracat Yonetmeligi",
        url="",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
        notes="Mevzuat.gov.tr uzerinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="yonetmelik-yan-hizmetler",
        title="Elektrik Piyasasi Yan Hizmetler Yonetmeligi",
        url="",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
        notes="Mevzuat.gov.tr uzerinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="yonetmelik-dengeleme-uzlastirma",
        title="Elektrik Piyasasi Dengeleme ve Uzlastirma Yonetmeligi",
        url="https://www.mevzuat.gov.tr/File/GeneratePdf?mevzuatNo=12985&mevzuatTur=KurumVeKurulusYonetmeligi&mevzuatTertip=5",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
        notes="Mevzuat No 12985, dogrulanmis. Elle indirildi.",
    ),
]


def direct_sources() -> list[SourceDoc]:'''

if anchor not in text:
    print("HATA: anchor bulunamadi.")
else:
    new_text = text.replace(anchor, new_entries)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili, 5 yeni kaynak eklendi.")
