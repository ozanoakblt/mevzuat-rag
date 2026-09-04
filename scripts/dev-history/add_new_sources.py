import pathlib

p = pathlib.Path("src/ingestion/sources.py")
text = p.read_text(encoding="utf-8")

anchor = "]\n\n\ndef direct_sources() -> list[SourceDoc]:"

new_entries = '''    SourceDoc(
        doc_id="yonetmelik-lisans",
        title="Elektrik Piyasasi Lisans Yonetmeligi",
        url="https://www.mevzuat.gov.tr/File/GeneratePdf?mevzuatNo=18985&mevzuatTur=KurumVeKurulusYonetmeligi&mevzuatTertip=5",
        fetch_type="direct_file",
        doc_type="yonetmelik",
    ),
    SourceDoc(
        doc_id="yonetmelik-tuketici-hizmetleri",
        title="Elektrik Piyasasi Tuketici Hizmetleri Yonetmeligi",
        url="https://www.mevzuat.gov.tr/File/GeneratePdf?mevzuatNo=24630&mevzuatTur=KurumVeKurulusYonetmeligi&mevzuatTertip=5",
        fetch_type="direct_file",
        doc_type="yonetmelik",
    ),
    SourceDoc(
        doc_id="yonetmelik-dagitim-sistemi",
        title="Elektrik Dagitim Sistemi Yonetmeligi",
        url="https://www.mevzuat.gov.tr/File/GeneratePdf?mevzuatNo=39469&mevzuatTur=KurumVeKurulusYonetmeligi&mevzuatTertip=5",
        fetch_type="direct_file",
        doc_type="yonetmelik",
        notes=(
            "14/3/2013 tarihli eski 'Elektrik Piyasasi Dagitim Yonetmeligi' "
            "(RG 28870) yerine gecmistir; eski yonetmelik mulgadir."
        ),
    ),
    SourceDoc(
        doc_id="yonetmelik-tarifeler",
        title="Elektrik Piyasasi Tarifeler Yonetmeligi",
        url="https://www.mevzuat.gov.tr/File/GeneratePdf?mevzuatNo=36105&mevzuatTur=KurumVeKurulusYonetmeligi&mevzuatTertip=5",
        fetch_type="direct_file",
        doc_type="yonetmelik",
    ),
    SourceDoc(
        doc_id="yonetmelik-osb",
        title=(
            "Organize Sanayi Bolgelerinin ve Endustri Bolgelerinin Elektrik "
            "Piyasasi Faaliyetlerine Iliskin Yonetmelik"
        ),
        url="https://www.mevzuat.gov.tr/File/GeneratePdf?mevzuatNo=40876&mevzuatTur=KurumVeKurulusYonetmeligi&mevzuatTertip=5",
        fetch_type="direct_file",
        doc_type="yonetmelik",
    ),
]


def direct_sources() -> list[SourceDoc]:'''

if anchor not in text:
    print("HATA: anchor bulunamadi, dosya degismedi.")
else:
    new_text = text.replace(anchor, new_entries)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili, 5 yeni kaynak eklendi.")
