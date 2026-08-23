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
            "Hizmet Kalitesi Yönetmeliği (Son Versiyon)"
        ),
        url="https://www.epdk.gov.tr/Detay/Icerik/12-3/elektrik",
        fetch_type="needs_resolution",
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
]


def direct_sources() -> list[SourceDoc]:
    return [s for s in SOURCES if s.fetch_type == "direct_file"]


def needs_resolution_sources() -> list[SourceDoc]:
    return [s for s in SOURCES if s.fetch_type == "needs_resolution"]