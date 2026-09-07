"""
Faz 1 için sabit kaynak listesi (brief madde 5).

Otomatik keşif yok — sadece burada listelenen URL'ler işlenir.
Yeni kaynak eklemek için bu listeye yeni bir SourceDoc ekle.

fetch_type açıklaması:
  - "direct_file": URL doğrudan bir PDF/DOC dosyasına gider, indirilip
    hash'lenebilir. Faz 1'de otomatik işlenir.
  - "needs_resolution": URL bir "bilgi sayfası" ya da "listeleme sayfası";
    asıl belge linki bu sayfanın içinden bulunmalı. Sayfa yapısı elle
    doğrulanmadan otomatik indirme YAPILMAZ (brief: "varsayım yapıp
    ilerleme, sor" ilkesi) — script bunun yerine sayfayı indirip
    data/raw/_manual_review/ altına koyar, siz asıl belge linkini
    bulup bu dosyaya SourceDoc olarak eklersiniz.
"""
from dataclasses import dataclass
from typing import Literal

FetchType = Literal["direct_file", "needs_resolution"]


@dataclass(frozen=True)
class SourceDoc:
    doc_id: str
    title: str
    url: str
    fetch_type: FetchType
    doc_type: str  # "kanun" | "yonetmelik" | "listeleme" | "bilgi_sayfasi"
    notes: str = ""
    # Faz 2'deki metadata motoruna aktarılacak, belgenin "güncelliği" hakkında
    # bilinmesi gereken not (ör. "bu konsolide metin şu tarihli değişikliği
    # henüz içermiyor olabilir"). Boşsa herhangi bir uyarı yok demektir.
    completeness_note: str = ""


SOURCES: list[SourceDoc] = [
    SourceDoc(
        doc_id="epdk-yonetmelikler-listesi",
        title="EPDK Güncel Elektrik Piyasası Yönetmelikleri Listesi",
        url="https://www.epdk.gov.tr/Detay/Icerik/3-0-159-3/yonetmelikler",
        fetch_type="needs_resolution",
        doc_type="listeleme",
        notes=(
            "Ana keşif noktası. Faz 1'de içerik olarak ingest edilmeyecek; "
            "sadece gelecekteki yeni-belge taraması (madde 6) için ayrı bir "
            "modülde kullanılacak. Şimdilik SOURCES listesinde referans "
            "amaçlı duruyor."
        ),
    ),
    SourceDoc(
        doc_id="kanun-6446",
        title="6446 Sayılı Elektrik Piyasası Kanunu",
        url="https://www.mevzuat.gov.tr/mevzuatmetin/1.5.6446.pdf",
        fetch_type="direct_file",
        doc_type="kanun",
    ),
    # --- Elektrik Piyasası Bağlantı ve Sistem Kullanım Yönetmeliği ---
    # EPDK sayfasındaki versiyon tablosundan tespit edildi (bkz. proje notları):
    #   - "Son Versiyon" satırı: 27.01.2026, RG Sayı 33150  -> tam konsolide metin
    #   - "Değişiklik" satırı:   25.06.2026, RG Sayı 33291  -> Son Versiyon'dan
    #     DAHA YENİ. Yani 27.01.2026 tarihli tam metin, bu değişikliği henüz
    #     içermiyor olabilir. Karar: ikisi de indirilecek, tam metne
    #     completeness_note ile uyarı iğnelendi.
    # TODO: Word ikonlarının gerçek href'leri (url alanları) elle doldurulacak.
    SourceDoc(
        doc_id="yonetmelik-baglanti-sistem-kullanim-2026-01-27",
        title=(
            "Elektrik Piyasası Bağlantı ve Sistem Kullanım Yönetmeliği "
            "(Son Versiyon, 27.01.2026, RG 33150)"
        ),
        url="",  # EPDK bot koruması nedeniyle otomatik indirilemiyor; elle sağlandı.
        fetch_type="needs_resolution",  # otomatik hash-kontrolü URL olmadan yapılamaz
        doc_type="yonetmelik",
        completeness_note=(
            "27.01.2026 tarihli bu konsolide metin, 25.06.2026 tarihli "
            "değişikliği (RG 33291) İÇERMİYOR OLABİLİR. Query zamanında "
            "bu iki belge birlikte değerlendirilmeli; kullanıcıya "
            "'daha yeni bir değişiklik var, resmi metni kontrol edin' "
            "uyarısı verilmesi gerekebilir (Faz 9: hallucination guard "
            "kapsamında ele alınacak)."
        ),
    ),
    SourceDoc(
        doc_id="yonetmelik-baglanti-sistem-kullanim-2026-06-25-degisiklik",
        title=(
            "Elektrik Piyasası Bağlantı ve Sistem Kullanım Yönetmeliğinde "
            "Değişiklik (25.06.2026, RG 33291)"
        ),
        url="",  # TODO: EPDK tablosundaki 25.06.2026 "Değişiklik" satırının Word linki
        fetch_type="needs_resolution",
        doc_type="yonetmelik_degisiklik",
        completeness_note=(
            "Bu belge tam metin değil, yalnızca değişiklik metnidir. "
            "İlgili tam metin: yonetmelik-baglanti-sistem-kullanim-2026-01-27."
        ),
    ),
    SourceDoc(
        doc_id="yonetmelik-hizmet-kalitesi",
        title=(
            "Elektrik Dağıtımı ve Perakende Satışına İlişkin "
            "Hizmet Kalitesi Yönetmeliği (ESKI/MULGA - yerine "
            "yonetmelik-kalite-guncel (Mevzuat No 36132) gecti)"
        ),
        url="https://www.epdk.gov.tr/Detay/Icerik/12-3/elektrik",
        fetch_type="disabled",
        doc_type="yonetmelik",
        notes="EPDK bilgi sayfası üzerinden asıl metne ulaşılacak (brief madde 5).",
    ),
    SourceDoc(
        doc_id="yonetmelik-hizmet-kalitesi-degisiklik",
        title=(
            "Elektrik Dağıtımı ve Perakende Satışına İlişkin Hizmet Kalitesi "
            "Yönetmeliğinde Değişiklik (varsa, Son Versiyon'dan daha yeni)"
        ),
        url="https://www.epdk.gov.tr/Detay/Icerik/12-3/elektrik",
        fetch_type="needs_resolution",
        doc_type="yonetmelik_degisiklik",
        notes=(
            "Sadece EPDK tablosunda 'Son Versiyon' satırından DAHA YENİ "
            "tarihli bir 'Değişiklik' satırı varsa doldurulur. Yoksa bu "
            "kaynağı boş bırakın, sync bu doc_id'yi atlar."
        ),
    ),
    SourceDoc(
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
    SourceDoc(
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
    SourceDoc(
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
    SourceDoc(
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
    SourceDoc(
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
    SourceDoc(
        doc_id="yonetmelik-seffaflik-piyasa-bozucu",
        title="Enerji Piyasalarinda ve Cevresel Piyasalarda Seffafliga ve Piyasa Bozucu Davranislara Iliskin Yonetmelik",
        url="",
        fetch_type="needs_resolution",
        doc_type="yonetmelik",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-dgp-etiket-smf",
        title="Dengeleme Guc Piyasasi Kapsaminda Etiket Degerlerinin Belirlenmesi ve Sistem Marjinal Fiyatinin Hesaplanmasi Proseduru",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-teminat-hesaplama-yontemi",
        title="Teminat Hesaplama Yontemi",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-gop-teklif",
        title="Gun Oncesi Piyasasi Tekliflerinin Yapisi ve Tekliflerin Degerlendirilmesine Iliskin Usul ve Esaslar",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-fiyat-limitleri",
        title="Gun Oncesi Piyasasinda ve Dengeleme Guc Piyasasinda Asgari ve Azami Fiyat Limitlerinin Belirlenmesine Iliskin Usul ve Esaslar",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-teminat-esaslari",
        title="Teminat Usul ve Esaslari (TUE)",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-tahmini-tuketim-degeri",
        title="Tahmini Tuketim Degeri Belirleme Metodolojisi",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-toplam-tuketim-tahmini",
        title="Toplam Tuketim Tahmini Belirleme Metodolojisi",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-akilli-sayac",
        title="Akilli Sayac Sistemlerinin Yayginlastirilmasina ve Kullanimina Iliskin Usul ve Esaslar",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-tarife-uygulama",
        title="Dagitim Lisansi Sahibi Tuzel Kisiler ve Gorevli Tedarik Sirketlerinin Tarife Uygulamalarina Iliskin Usul ve Esaslar",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-kayip-katsayilari",
        title="Kayip Katsayilari Hesaplama Metodolojisine Iliskin Usul ve Esaslar",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-destekleme-bedeli",
        title="Kaynak Bazinda Destekleme Bedelinin Belirlenmesine ve Uygulanmasina Iliskin Usul ve Esaslar",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-osos",
        title="Otomatik Sayac Okuma Sistemlerinin Kapsamina ve Sayac Degerlerinin Belirlenmesine Iliskin Usul ve Esaslar",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-talep-tarafi-sapma",
        title="Talep Tarafi Katilimi Hizmeti Kapsaminda Temel Tuketim Degerinden Sapma Tutarinin Belirlenmesine Iliskin Usul ve Esaslar",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-profil-uygulamasi",
        title="Uzlastirma Hesaplamalarinda Kullanilacak Profil Uygulamasina Iliskin Usul ve Esaslar",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-vep",
        title="Vadeli Elektrik Piyasasi Isletim Usul ve Esaslari",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-onlisans-basvuru-belgeleri",
        title="Onlisans ve Lisans Islemleri ile Ilgili Basvurulara Iliskin Usul ve Esaslar - Onlisans Basvuru Belgeleri Listesi",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-lisans-basvuru-belgeleri",
        title="Onlisans ve Lisans Islemleri ile Ilgili Basvurulara Iliskin Usul ve Esaslar - Lisans Basvuru Belgeleri Listesi",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-tadil-devir-belgeleri",
        title="Onlisans ve Lisans Tadil Basvurulari ile Birlesme Bolunme Tesis-Proje Devri Onay Basvurularinda Sunulmasi Gereken Bilgi ve Belgeler Listesi",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-fark-tutari",
        title="Fark Tutari Proseduru",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-karsiliksiz-islemler",
        title="Karsiligi Olmayan Piyasa Islemlerine Iliskin Yontem",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-teknik-kalite",
        title="Elektrik Dagitim Sisteminin Teknik Kalitesine Iliskin Usul ve Esaslar",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-cbs",
        title="Elektrik Dagitim Sirketleri Tarafindan Kurulan Cografi Bilgi Sistemlerinin Iyilestirilmesine ve Standartlastirilmasina Yonelik Usul ve Esaslar",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-santral-sahalari",
        title="Elektrik Piyasasinda Onlisans veya Lisanslara Konu Uretim Tesislerinin Santral Sahalarinin Belirlenmesine Iliskin Usul ve Esaslar",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-ithalat-ihracat-uzlastirma",
        title="Elektrik Piyasasinda Ithalat ve Ihracata Iliskin Uzlastirma Usul ve Esaslari",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
    SourceDoc(
        doc_id="usul-hat-katilim-bedeli",
        title="Hat Katilim Bedelinin Belirlenmesine Dair Usul ve Esaslar",
        url="",
        fetch_type="needs_resolution",
        doc_type="usul-esas",
        notes="EPDK sitesinden bulundu, elle indirildi.",
    ),
]


def direct_sources() -> list[SourceDoc]:
    return [s for s in SOURCES if s.fetch_type == "direct_file"]


def needs_resolution_sources() -> list[SourceDoc]:
    return [s for s in SOURCES if s.fetch_type == "needs_resolution"]