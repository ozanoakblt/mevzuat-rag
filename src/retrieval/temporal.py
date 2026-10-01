"""
Faz 14: Temporal/version-aware retrieval.

Ayni duzenlemenin birden fazla tarihli versiyonu korpusta AYRI birer
SourceDoc olarak bulunabiliyor (orn. Baglanti ve Sistem Kullanim
Yonetmeligi'nin 27.01.2026 konsolide metni + 25.06.2026 degisikligi,
bkz. sources.py'deki version_group/effective_from alanlari). Bu ikisi
retrieval'da ESIT agirlikla yarisir - hangisinin secildigi, sorgunun
hangi tarihi kastettigine bakilmaksizin, saf anlamsal/BM25 benzerligine
kalir. Bu modul iki sey yapar:

1. Sorudan bir "sorgu tarihi" cikarmaya calisir (orn. "2026 Haziran
   itibariyla", "27.01.2026 tarihinden once" gibi ifadelerden).
2. Ayni version_group'taki adaylar arasinda, sorgu tarihine gore
   GECERLI olan (effective_from <= sorgu tarihi) en GUNCEL versiyonu
   one cikarir - sorguda tarih YOKSA varsayilan olarak en guncel
   versiyon tercih edilir (kullanicilar aksini belirtmedikce "su anki
   mevzuat" sorulduğu varsayilir).

Not: answer_generator.py'deki SYSTEM_PROMPT kural 5d zaten metin
icindeki (Mulga:...)/(Degisik:RG-...) notasyonlarina bakarak bir
olcude versiyon celiskisini cozuyor - bu modul, o celismeyi modelin
ONUNE HIC GETIRMEDEN, retrieval asamasinda COZMEYE calisir (defense
in depth - aynı projedeki diger "deterministik katman + LLM" ikilisi
felsefesiyle tutarli).
"""
from __future__ import annotations

import re
from datetime import date

_TURKISH_MONTHS = {
    "ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4, "mayıs": 5, "mayis": 5,
    "haziran": 6, "temmuz": 7, "ağustos": 8, "agustos": 8, "eylül": 9, "eylul": 9,
    "ekim": 10, "kasım": 11, "kasim": 11, "aralık": 12, "aralik": 12,
}

# "27.01.2026" / "27/01/2026"
_EXPLICIT_DATE_RE = re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b")
# "2026 Haziran" / "Haziran 2026" / "2026 yılı Haziran ayı"
_MONTH_YEAR_RE = re.compile(
    r"\b(?:(\d{4})\s+(?:yılı\s+)?([A-Za-zÇĞİÖŞÜçğıöşü]+)|([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(\d{4}))\b"
)
# Bare yil: "2026 itibarıyla", "2026'da", "2026 yılında"
_YEAR_RE = re.compile(r"\b(20\d{2})\b")


def extract_query_date(question: str) -> date | None:
    """
    Soru metninden bir tarih cikarmaya calisir. Bulamazsa None doner -
    bu durumda caller "varsayilan: en guncel versiyon" davranisini
    uygulamalidir (bkz. modul docstring'i).
    """
    m = _EXPLICIT_DATE_RE.search(question)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(year, month, day)
        except ValueError:
            pass  # gecersiz tarih (orn. 31/02) - diger kaliplere dus

    m = _MONTH_YEAR_RE.search(question)
    if m:
        if m.group(1):
            year, month_word = int(m.group(1)), m.group(2).lower()
        else:
            month_word, year = m.group(3).lower(), int(m.group(4))
        # Turkce hal ekleri kelimeye bitisik gelebilir ("Haziran'ında",
        # "Haziranında") - ay adinin KOKU ile baslayan herhangi bir
        # kelimeyi kabul ediyoruz (en uzun esleseni tercih ederek "mart"
        # gibi kisa bir kokun baska bir ayin icinde yanlislikla
        # eslesmesini onluyoruz).
        month = next(
            (mo for stem, mo in sorted(_TURKISH_MONTHS.items(), key=lambda kv: -len(kv[0]))
             if month_word.startswith(stem)),
            None,
        )
        if month:
            return date(year, month, 1)

    m = _YEAR_RE.search(question)
    if m:
        return date(int(m.group(1)), 1, 1)

    return None


# Sorguda hicbir tarih bulunamazsa, ayni version_group icindeki adaylar
# arasindan bu kadar GUCLU bir carpanla en GUNCEL versiyon one cikarilir
# (kullanicilar aksini belirtmedikce "su anki mevzuat" kastedilir).
DEFAULT_LATEST_BOOST = 1.5
# Sorguda bir tarih varsa ve bir versiyon o tarihte HENUZ YURURLUKTE
# DEGILSE (effective_from > sorgu tarihi), bu kadar guclu bir carpanla
# geri plana itilir - TAMAMEN elenmez (nadir durumlarda kullanici bilerek
# "eski metne gore" sorabilir, o yuzden sert bir filtre yerine yumusak
# bir ceza tercih edildi).
FUTURE_VERSION_PENALTY = 0.3


def apply_temporal_adjustment(
    results: list[dict],
    query_date: date | None,
    doc_versions: dict[str, tuple[str, date]],
) -> None:
    """
    results: hybrid_search ciktisi (rrf_score alanlari YERINDE degistirilir).
    doc_versions: {doc_id: (version_group, effective_from)} - version_group'u
    olmayan (tekil) belgeler bu sozlukte YOKTUR, dokunulmaz.

    version_group'u paylasan adaylar arasinda en az 2 FARKLI doc_id
    gercekten sonuclarda bulunmuyorsa hicbir islem yapilmaz (tek versiyon
    zaten mevcutsa secim belirsizligi yok, boost gereksiz).
    """
    groups: dict[str, set[str]] = {}
    for r in results:
        info = doc_versions.get(r.get("doc_id"))
        if info:
            groups.setdefault(info[0], set()).add(r["doc_id"])

    contested_groups = {g for g, docs in groups.items() if len(docs) > 1}
    if not contested_groups:
        return

    # Her tartismali grup icin en guncel effective_from'u BIR KEZ hesapla
    # (dongude her sonuc icin tekrar hesaplamak yerine).
    latest_by_group = {
        g: max(
            effective_from_g
            for doc_id_g, (group_g, effective_from_g) in doc_versions.items()
            if group_g == g and doc_id_g in docs
        )
        for g, docs in groups.items()
        if g in contested_groups
    }

    for r in results:
        info = doc_versions.get(r.get("doc_id"))
        if not info or info[0] not in contested_groups:
            continue
        group, effective_from = info

        if query_date is not None:
            if effective_from > query_date:
                r["rrf_score"] *= FUTURE_VERSION_PENALTY
            continue

        # Sorguda tarih yok: bu version_group'taki EN GUNCEL effective_from'a
        # sahip belgeyi one cikar.
        if effective_from == latest_by_group[group]:
            r["rrf_score"] *= DEFAULT_LATEST_BOOST
