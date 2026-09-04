import pathlib

p = pathlib.Path("src/ingestion/sources.py")
text = p.read_text(encoding="utf-8")

anchor = "]\n\n\ndef direct_sources() -> list[SourceDoc]:"

new_entries = '''    SourceDoc(
        doc_id="yonetmelik-kalite-guncel",
        title="Elektrik Piyasasinda Dagitim ve Perakende Satis Faaliyetlerine Iliskin Kalite Yonetmeligi",
        url="https://www.mevzuat.gov.tr/File/GeneratePdf?mevzuatNo=36132&mevzuatTur=KurumVeKurulusYonetmeligi&mevzuatTertip=5",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
        notes="Eski yonetmelik-hizmet-kalitesi.docx yerine gecen guncel versiyon (Mevzuat No 36132). Eski dosya .mulga uzantisiyla devre disi.",
    ),
    SourceDoc(
        doc_id="tebliğ-dagitim-tarifesi",
        title="Dagitim Tarifesinin Duzenlenmesi Hakkinda Teblig",
        url="https://www.mevzuat.gov.tr/File/GeneratePdf?mevzuatNo=36089&mevzuatTur=Teblig&mevzuatTertip=5",
        fetch_type="needs_resolution",
        doc_type="teblig",
    ),
    SourceDoc(
        doc_id="tebliğ-perakende-satis-tarifesi",
        title="Perakende Satis Tarifesinin Duzenlenmesi Hakkinda Teblig",
        url="https://www.mevzuat.gov.tr/File/GeneratePdf?mevzuatNo=36106&mevzuatTur=Teblig&mevzuatTertip=5",
        fetch_type="needs_resolution",
        doc_type="teblig",
    ),
    SourceDoc(
        doc_id="tebliğ-son-kaynak-tedarik-tarifesi",
        title="Son Kaynak Tedarik Tarifesinin Duzenlenmesi Hakkinda Teblig",
        url="https://www.mevzuat.gov.tr/File/GeneratePdf?mevzuatNo=24339&mevzuatTur=Teblig&mevzuatTertip=5",
        fetch_type="needs_resolution",
        doc_type="teblig",
    ),
    SourceDoc(
        doc_id="tebliğ-piyasa-isletim-geliri",
        title="Piyasa Isletim Gelirinin Duzenlenmesi Hakkinda Teblig",
        url="",
        fetch_type="needs_resolution",
        doc_type="teblig",
    ),
    SourceDoc(
        doc_id="tebliğ-fiyat-esitleme",
        title="Fiyat Esitleme Mekanizmasi Tebligi",
        url="",
        fetch_type="needs_resolution",
        doc_type="teblig",
    ),
    SourceDoc(
        doc_id="tebliğ-dagitim-baglanti-bedelleri",
        title="Elektrik Piyasasinda Dagitim Baglanti Bedellerinin Belirlenmesi Hakkinda Teblig",
        url="",
        fetch_type="needs_resolution",
        doc_type="teblig",
    ),
    SourceDoc(
        doc_id="yonetmelik-res-ges-yarisma",
        title="Ruzgar veya Gunes Enerjisine Dayali Uretim Tesisi Kurmak Uzere Yapilan Onlisans Basvurularina Iliskin Yarisma Yonetmeligi",
        url="",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
    ),
    SourceDoc(
        doc_id="yonetmelik-denetim-sorusturma",
        title="Elektrik Piyasasinda Yapilacak Denetimler Ile On Arastirma ve Sorusturmalarda Takip Edilecek Usul ve Esaslar Hakkinda Yonetmelik",
        url="",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
    ),
    SourceDoc(
        doc_id="yonetmelik-kayip-azaltma",
        title="Dagitim Sistemindeki Kayiplarin Azaltilmasina Dair Tedbirler Yonetmeligi",
        url="",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
    ),
    SourceDoc(
        doc_id="yonetmelik-bildirim",
        title="Enerji Piyasasi Bildirim Yonetmeligi",
        url="",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
    ),
    SourceDoc(
        doc_id="yonetmelik-olcum-sistemleri",
        title="Elektrik Piyasasi Olcum Sistemleri Yonetmeligi",
        url="",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
    ),
    SourceDoc(
        doc_id="yonetmelik-yek-belgelendirme",
        title="Yenilenebilir Enerji Kaynaklarinin Belgelendirilmesi ve Desteklenmesine Iliskin Yonetmelik",
        url="",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
    ),
    SourceDoc(
        doc_id="yonetmelik-toplayicilik",
        title="Elektrik Piyasasinda Toplayicilik Faaliyeti Yonetmeligi",
        url="",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
    ),
    SourceDoc(
        doc_id="yonetmelik-depolama",
        title="Elektrik Piyasasinda Depolama Faaliyetleri Yonetmeligi",
        url="",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
    ),
    SourceDoc(
        doc_id="yonetmelik-talep-tahminleri",
        title="Elektrik Piyasasi Talep Tahminleri Yonetmeligi",
        url="",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
    ),
    SourceDoc(
        doc_id="yonetmelik-kapasite-mekanizmasi",
        title="Elektrik Piyasasi Kapasite Mekanizmasi Yonetmeligi",
        url="",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
    ),
]


def direct_sources() -> list[SourceDoc]:'''

if anchor not in text:
    print("HATA: anchor bulunamadi.")
else:
    new_text = text.replace(anchor, new_entries)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili, 17 yeni kaynak eklendi.")
