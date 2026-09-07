import pathlib

p = pathlib.Path("src/ingestion/sources.py")
text = p.read_text(encoding="utf-8")

anchor = "]\n\n\ndef direct_sources() -> list[SourceDoc]:"

new_entries = '''    SourceDoc(
        doc_id="yonetmelik-tadiller-devir",
        title="Elektrik Piyasasinda Birden Fazla Piyasa Faaliyetini Surdurmekte Olan Tuzel Kisilerin Mevcut Sozlesmelerinde Yapilacak Tadillere ve Iletim Faaliyeti ile Vazgecilen Faaliyetlerin Devrine Iliskin Yonetmelik",
        url="",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="yonetmelik-bilisim-guvenligi",
        title="Enerji Sektorunde Kullanilan Endustriyel Kontrol Sistemlerinde Bilisim Guvenligi Yonetmeligi",
        url="",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="yonetmelik-epias-teskilat",
        title="Enerji Piyasalari Isletme Anonim Sirketi Teskilat Yapisi ve Calisma Esaslari Hakkinda Yonetmelik",
        url="",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
    ),
    SourceDoc(
        doc_id="yonetmelik-yek-g",
        title="Elektrik Piyasasinda Yenilenebilir Enerji Kaynak Garanti Belgesi Yonetmeligi",
        url="",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
    ),
    SourceDoc(
        doc_id="yonetmelik-tedbirler",
        title="Elektrik Piyasasinda Dagitim ve Tedarik Lisanslarina Iliskin Tedbirler Yonetmeligi",
        url="",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
    ),
    SourceDoc(
        doc_id="yonetmelik-satin-alma-satis",
        title="Elektrik Dagitim Sirketlerinin Satin Alma ve Satis Islemleri Uygulama Yonetmeligi",
        url="",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
        notes="Mevzuat No 36119.",
    ),
]


def direct_sources() -> list[SourceDoc]:'''

if anchor not in text:
    print("HATA: anchor bulunamadi.")
else:
    new_text = text.replace(anchor, new_entries)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili, 6 yeni kaynak eklendi.")
