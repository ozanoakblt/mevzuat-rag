import pathlib

p = pathlib.Path("src/ingestion/sources.py")
text = p.read_text(encoding="utf-8")

anchor = "]\n\n\ndef direct_sources() -> list[SourceDoc]:"

entries = [
    ("yonetmelik-seffaflik-piyasa-bozucu", "Enerji Piyasalarinda ve Cevresel Piyasalarda Seffafliga ve Piyasa Bozucu Davranislara Iliskin Yonetmelik", "yonetmelik"),
    ("usul-dgp-etiket-smf", "Dengeleme Guc Piyasasi Kapsaminda Etiket Degerlerinin Belirlenmesi ve Sistem Marjinal Fiyatinin Hesaplanmasi Proseduru", "usul-esas"),
    ("usul-teminat-hesaplama-yontemi", "Teminat Hesaplama Yontemi", "usul-esas"),
    ("usul-gop-teklif", "Gun Oncesi Piyasasi Tekliflerinin Yapisi ve Tekliflerin Degerlendirilmesine Iliskin Usul ve Esaslar", "usul-esas"),
    ("usul-fiyat-limitleri", "Gun Oncesi Piyasasinda ve Dengeleme Guc Piyasasinda Asgari ve Azami Fiyat Limitlerinin Belirlenmesine Iliskin Usul ve Esaslar", "usul-esas"),
    ("usul-teminat-esaslari", "Teminat Usul ve Esaslari (TUE)", "usul-esas"),
    ("usul-tahmini-tuketim-degeri", "Tahmini Tuketim Degeri Belirleme Metodolojisi", "usul-esas"),
    ("usul-toplam-tuketim-tahmini", "Toplam Tuketim Tahmini Belirleme Metodolojisi", "usul-esas"),
    ("usul-akilli-sayac", "Akilli Sayac Sistemlerinin Yayginlastirilmasina ve Kullanimina Iliskin Usul ve Esaslar", "usul-esas"),
    ("usul-tarife-uygulama", "Dagitim Lisansi Sahibi Tuzel Kisiler ve Gorevli Tedarik Sirketlerinin Tarife Uygulamalarina Iliskin Usul ve Esaslar", "usul-esas"),
    ("usul-kayip-katsayilari", "Kayip Katsayilari Hesaplama Metodolojisine Iliskin Usul ve Esaslar", "usul-esas"),
    ("usul-destekleme-bedeli", "Kaynak Bazinda Destekleme Bedelinin Belirlenmesine ve Uygulanmasina Iliskin Usul ve Esaslar", "usul-esas"),
    ("usul-osos", "Otomatik Sayac Okuma Sistemlerinin Kapsamina ve Sayac Degerlerinin Belirlenmesine Iliskin Usul ve Esaslar", "usul-esas"),
    ("usul-talep-tarafi-sapma", "Talep Tarafi Katilimi Hizmeti Kapsaminda Temel Tuketim Degerinden Sapma Tutarinin Belirlenmesine Iliskin Usul ve Esaslar", "usul-esas"),
    ("usul-profil-uygulamasi", "Uzlastirma Hesaplamalarinda Kullanilacak Profil Uygulamasina Iliskin Usul ve Esaslar", "usul-esas"),
    ("usul-vep", "Vadeli Elektrik Piyasasi Isletim Usul ve Esaslari", "usul-esas"),
    ("usul-onlisans-basvuru-belgeleri", "Onlisans ve Lisans Islemleri ile Ilgili Basvurulara Iliskin Usul ve Esaslar - Onlisans Basvuru Belgeleri Listesi", "usul-esas"),
    ("usul-lisans-basvuru-belgeleri", "Onlisans ve Lisans Islemleri ile Ilgili Basvurulara Iliskin Usul ve Esaslar - Lisans Basvuru Belgeleri Listesi", "usul-esas"),
    ("usul-tadil-devir-belgeleri", "Onlisans ve Lisans Tadil Basvurulari ile Birlesme Bolunme Tesis-Proje Devri Onay Basvurularinda Sunulmasi Gereken Bilgi ve Belgeler Listesi", "usul-esas"),
    ("usul-fark-tutari", "Fark Tutari Proseduru", "usul-esas"),
    ("usul-karsiliksiz-islemler", "Karsiligi Olmayan Piyasa Islemlerine Iliskin Yontem", "usul-esas"),
    ("usul-teknik-kalite", "Elektrik Dagitim Sisteminin Teknik Kalitesine Iliskin Usul ve Esaslar", "usul-esas"),
    ("usul-cbs", "Elektrik Dagitim Sirketleri Tarafindan Kurulan Cografi Bilgi Sistemlerinin Iyilestirilmesine ve Standartlastirilmasina Yonelik Usul ve Esaslar", "usul-esas"),
    ("usul-santral-sahalari", "Elektrik Piyasasinda Onlisans veya Lisanslara Konu Uretim Tesislerinin Santral Sahalarinin Belirlenmesine Iliskin Usul ve Esaslar", "usul-esas"),
    ("usul-ithalat-ihracat-uzlastirma", "Elektrik Piyasasinda Ithalat ve Ihracata Iliskin Uzlastirma Usul ve Esaslari", "usul-esas"),
    ("usul-hat-katilim-bedeli", "Hat Katilim Bedelinin Belirlenmesine Dair Usul ve Esaslar", "usul-esas"),
]

new_entries_text = "".join(
    f'''    SourceDoc(
        doc_id="{doc_id}",
        title="{title}",
        url="",
        fetch_type="needs_resolution",
        doc_type="{doc_type}",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
'''
    for doc_id, title, doc_type in entries
)

new_block = new_entries_text + "]\n\n\ndef direct_sources() -> list[SourceDoc]:"

if anchor not in text:
    print("HATA: anchor bulunamadi.")
else:
    new_text = text.replace(anchor, new_block)
    p.write_text(new_text, encoding="utf-8")
    print(f"Basarili, {len(entries)} yeni kaynak eklendi.")
