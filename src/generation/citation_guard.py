"""
Faz 9: Citation + hallucination guard.

İki bağımsız kontrol katmanı:
  1. Güven eşiği: retrieval'ın en iyi rerank skoru düşükse (Faz 7'de
     gördüğümüz gibi, negatif skor = zayıf eşleşme), cevaba otomatik bir
     düşük-güven uyarısı ekleriz — modelin kendi ifadesine güvenmek yerine.
  2. Alıntı doğrulama: modelin cevabının sonuna eklediği "Kaynak
     Alıntıları" bölümündeki her alıntının, GERÇEKTEN ilgili kaynak
     pasajda birebir geçip geçmediğini otomatik kontrol ederiz. Model
     alıntıyı uydurmuşsa (ya da hafızadan yanlış hatırlamışsa), bunu
     kullanıcıya açıkça bildiririz — sessizce güvenilir gibi sunmayız.

Bu kontroller modelin "iyi davranmasına" güvenmek yerine, çıktısını
programatik olarak denetler (defense in depth — brief madde 13'teki
kurallara prompt seviyesinde uymak yeterli değil, doğrulanmalı).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

LOW_CONFIDENCE_RERANK_THRESHOLD = 0.0

_CITATION_QUOTE_RE = re.compile(r'\[(\d+)\]:\s*"([^"]+)"')


_TURKISH_NUMBER_WORDS = {
    "sıfır": "0", "bir": "1", "iki": "2", "üç": "3", "dört": "4",
    "beş": "5", "altı": "6", "yedi": "7", "sekiz": "8", "dokuz": "9",
    "on": "10", "yirmi": "20", "otuz": "30", "kırk": "40", "elli": "50",
    "altmış": "60", "yetmiş": "70", "seksen": "80", "doksan": "90",
    "yüz": "100", "bin": "1000",
}


def _turkish_word_to_number(word: str) -> int | None:
    """
    Basit birlesik Turkce sayi kelimelerini (ornegin 'altmis', 'yuz yirmi',
    'iki yuz') tam sayiya cevirir. Sadece bu projede mevzuat metinlerinde
    goruleun sinirli aralik (0-999 civari mesafe/sure degerleri) icin
    yeterlidir - genel amacli bir sayi ayristirici degildir.
    """
    parts = word.lower().replace("i", "i").split()
    total = 0
    current = 0
    for part in parts:
        val = _TURKISH_NUMBER_WORDS.get(part)
        if val is None:
            return None
        val = int(val)
        if val == 100 or val == 1000:
            current = (current or 1) * val
            total += current
            current = 0
        else:
            current += val
    return total + current if (total or current) else None


def _normalize_turkish_numbers(text: str) -> str:
    """
    Metindeki Turkce yaziyla sayilari (ornegin 'altmis metre', 'yuz yirmi
    gun') rakama cevirir (ornegin '60 metre', '120 gun'). Bu, kaynak
    metinde yaziyla ('doksan gun') yazilan bir sayinin, modelin rakamla
    ('90 gun') yazdigi ayni degerle citation guard tarafindan farkli
    sanilip yanlislikla "dogrulanamadi" olarak isaretlenmesini onler -
    bu, gercek bir halusinasyon degil, sadece yazim bicimi farkidir.
    """
    number_word_pattern = r"\b(" + "|".join(_TURKISH_NUMBER_WORDS.keys()) + r")(\s+(" + "|".join(_TURKISH_NUMBER_WORDS.keys()) + r"))*\b"

    def _replace(match: "re.Match") -> str:
        num = _turkish_word_to_number(match.group(0))
        return str(num) if num is not None else match.group(0)

    return re.sub(number_word_pattern, _replace, text, flags=re.IGNORECASE)


_TYPOGRAPHIC_VARIANTS = {
    "\u2019": "'", "\u2018": "'",
    "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-",
}


_AMENDMENT_ANNOTATION_RE = re.compile(
    r"\(\s*(?:Değişik|Ek|Mülga)(?:\s+ibare)?\s*:[^)]*\)\d*",
    re.IGNORECASE,
)


def _strip_amendment_annotations(text: str) -> str:
    """
    RG kaynakli "(Değişik:RG-.../...)", "(Ek:RG-.../...)",
    "(Değişik ibare:RG-.../...)" gibi degisiklik notlarini - ve bunlara
    PDF cikariminda bazen boslukusuz yapisan artik rakamlari (orn.
    "(...)1 bentleri") - metinden temizler. Bu notlar mevzuatin
    SUBSTANCE'i degil, RG referans/gecmis bilgisi; model okunabilir bir
    cevap uretirken bunlari (haklı olarak) atlayabiliyor, bizim birebir
    alinti karsilastirmamiz bunu yanlislikla "uyusmuyor" saymamali.
    """
    return _AMENDMENT_ANNOTATION_RE.sub("", text)


def _normalize_typography(text: str) -> str:
    """
    Kaynak PDF'lerdeki Turkce tipografik kesme isareti (’, ornegin
    "MW’i", "km’den") ile modelin urettigi DUZ kesme isaretini (')
    esitler - LLM'ler metin uretirken bu tipografik karakterleri sik sik
    sadelestirir, bu da aksi halde dogru olan bir alintinin sadece bu
    karakter farkindan "dogrulanamadi" olarak yanlislikla isaretlenmesine
    yol acar.
    """
    for variant, canonical in _TYPOGRAPHIC_VARIANTS.items():
        text = text.replace(variant, canonical)
    return text


def _normalize(text: str) -> str:
    """
    Karşılaştırma için: TÜM boşlukları kaldır, küçük harfe çevir, ve
    tipografik karakter farklarını esitler.
    """
    text = _normalize_turkish_numbers(text)
    text = _normalize_typography(text)
    text = _strip_amendment_annotations(text)
    return re.sub(r"\s+", "", text.strip()).lower()


@dataclass
class CitationCheck:
    citation_num: int
    quote: str
    grounded: bool  # alıntı, gösterdiği kaynakta gerçekten var mı


@dataclass
class GuardResult:
    is_low_confidence: bool
    best_rerank_score: float | None
    citation_checks: list[CitationCheck] = field(default_factory=list)
    suspicious_numbers: list[str] = field(default_factory=list)
    uncited_negative_conclusions: list[str] = field(default_factory=list)

    @property
    def has_ungrounded_citations(self) -> bool:
        return any(not c.grounded for c in self.citation_checks)


def check_confidence(
    chunks: list[dict], threshold: float = LOW_CONFIDENCE_RERANK_THRESHOLD
) -> tuple[bool, float | None]:
    """En iyi rerank skoru eşiğin altındaysa (ya da hiç skor yoksa) düşük
    güven olarak işaretler."""
    scores = [c["rerank_score"] for c in chunks if "rerank_score" in c]
    if not scores:
        return True, None
    best = max(scores)
    return best < threshold, best


_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")

_LAW_NUMBER_CONTEXT_RE = re.compile(r"\b(\d+)\s+sayılı\b", re.IGNORECASE)

_ARTICLE_NUMBER_CONTEXT_RE = re.compile(
    r"\b(?:madde|fıkra|bent)\s*\(?(\d+)\)?\b"
    r"|\b(\d+)\s*(?:inci|ıncı|ncı|nci|uncu|üncü)?\s+(?:madde|fıkra|bent)\w*\b",
    re.IGNORECASE,
)

_DATE_RE = re.compile(r"\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b")


def check_numeric_consistency(answer_text: str, chunks: list[dict]) -> list[str]:
    """
    Cevap metnindeki sayisal degerlerin, kaynak pasajlarin herhangi
    birinde gecip gecmedigini kontrol eder. Su durumlar kontrol disi
    tutulur:
    - Tek/cift basamaksiz kucuk sayilar (0-9)
    - "<sayi> sayili <Kanun/Yonetmelik>" (kanun numarasi)
    - "Madde <sayi>" / "<sayi> uncu madde" / "fikra (<sayi>)" (madde/fikra/
      bent numarasi)
    - Tarihler (27.01.2026, 5/6/2023 gibi)
    """
    combined_source = _normalize_turkish_numbers(
        "\n".join(c["text"] for c in chunks)
    )

    text_without_dates = _DATE_RE.sub(" ", answer_text)
    answer_numbers = set(_NUMBER_RE.findall(_normalize_turkish_numbers(text_without_dates)))

    law_reference_numbers = {
        m.group(1) for m in _LAW_NUMBER_CONTEXT_RE.finditer(answer_text)
    }
    article_reference_numbers = {
        m.group(1) or m.group(2)
        for m in _ARTICLE_NUMBER_CONTEXT_RE.finditer(answer_text)
    }

    suspicious = []
    for num in sorted(answer_numbers):
        if num in law_reference_numbers or num in article_reference_numbers:
            continue
        bare_digits = num.replace(".", "").replace(",", "")
        if len(bare_digits) < 2:
            continue
        if num not in combined_source:
            suspicious.append(num)
    return suspicious


_NEGATIVE_CONCLUSION_RE = re.compile(
    r"[^.!?\n]*\b(yapılamaz|yapilamaz|mümkün değildir|mumkun degildir|"
    r"yasaktır|yasaktir|izin verilmez|uygulanamaz|geçerli değildir|"
    r"gecerli degildir|sağlanmamaktadır|saglanmamaktadir|"
    r"imkan(?:sızdır|sizdir))[^.!?\n]*[.!?]",
    re.IGNORECASE,
)
_CITATION_MARKER_IN_SENTENCE_RE = re.compile(r"\[\d+\]")


def check_uncited_negative_conclusion(answer_text: str) -> list[str]:
    """
    Cevap govdesinde (alinti blogu haric) yapilamaz/yasaktir/mumkun
    degildir gibi OLUMSUZ bir sonuc iceren ama icinde hicbir [N] alinti
    referansi OLMAYAN cumleleri tespit eder - modelin kendi mantiksal
    cikarimiyla urettigi bir yasak sonucu olabilecegini gosteren isaret.
    """
    body = answer_text.split("Kaynak Alıntıları:")[0]
    suspicious = []
    for match in _NEGATIVE_CONCLUSION_RE.finditer(body):
        sentence = match.group(0)
        if not _CITATION_MARKER_IN_SENTENCE_RE.search(sentence):
            suspicious.append(sentence.strip())
    return suspicious


def extract_citation_quotes(answer_text: str) -> dict[int, str]:
    """Cevabın sonundaki 'Kaynak Alıntıları: [1]: "..."' bölümünü ayrıştırır."""
    return {int(num): quote for num, quote in _CITATION_QUOTE_RE.findall(answer_text)}


def verify_citations(answer_text: str, chunks: list[dict]) -> list[CitationCheck]:
    """
    Her [N]: "alıntı" için, alıntının chunks[N-1]'in gerçek metninde birebir
    (normalize edilmiş) geçip geçmediğini kontrol eder.
    """
    quotes = extract_citation_quotes(answer_text)
    checks: list[CitationCheck] = []
    for num, quote in quotes.items():
        idx = num - 1
        if idx < 0 or idx >= len(chunks):
            checks.append(CitationCheck(citation_num=num, quote=quote, grounded=False))
            continue
        source_text = _normalize(chunks[idx]["text"])
        grounded = _normalize(quote) in source_text
        checks.append(CitationCheck(citation_num=num, quote=quote, grounded=grounded))
    return checks


import re as _re

_INSTITUTION_CONFLATION_RE = _re.compile(
    r"(dağıtım\s+şirket\w*|TEİAŞ|EPDK)\s*"
    r"\((?:örneğin|ör\.?|yani|diğer\s+bir\s+deyişle|misal)?\s*"
    r"(dağıtım\s+şirket\w*|TEİAŞ|EPDK)\)",
    _re.IGNORECASE,
)


def detect_institution_conflation(answer_text: str) -> bool:
    """
    Modelin farkli kurumlari (TEIAS, dagitim sirketi, EPDK) birbirinin
    esanlamlisi gibi sunmasini tespit eder - ornegin "dagitim sirketi
    (TEIAS)" gibi bir ifade, bu iki AYRI tuzel kisiyi yanlislikla
    esitleme anlamina gelir (gercek bir vakada tespit edildi: model
    "Dagitim sirketinin (TEIAS) SCADA sistemi..." diye yazmisti, oysa
    kaynak metin sadece TEIAS'tan bahsediyordu, dagitim sirketinden
    hic bahsetmiyordu). Prompt kurali (kural 15) bunu her zaman
    onleyemedigi icin, kod seviyesinde ek bir guvenlik agi olarak
    eklendi - tespit edilirse otomatik dusuk guven tetiklenir.
    """
    for m in _INSTITUTION_CONFLATION_RE.finditer(answer_text):
        a, b = m.group(1).lower(), m.group(2).lower()
        a_norm = "dagitim" if "dağıtım" in a else a
        b_norm = "dagitim" if "dağıtım" in b else b
        if a_norm != b_norm:
            return True
    return False


def run_guard(answer_text: str, chunks: list[dict]) -> GuardResult:
    is_low_confidence, best_score = check_confidence(chunks)
    citation_checks = verify_citations(answer_text, chunks)
    # Kaynak pasajlar verilmisken cevapta HIC alinti cikarilamamissa
    # (kural 8'e gore her cevap alinti icermeli), bu kendi basina supheli
    # bir sinyaldir - modelin alinti blogunu sessizce atladigi (gercek bir
    # eksiklik) ya da retrieval'in konuyla ilgisiz ama esik-ustu skorlu bir
    # sonuc bulup modelin "bulamadim" tarzi cevap verdigi (negatif test
    # senaryosu) durumlarinin ikisini de yakalar - her ikisi de kullaniciya
    # dusuk guvenle sunulmali.
    has_no_citations = bool(chunks) and not citation_checks
    has_ungrounded = any(not c.grounded for c in citation_checks)
    has_conflation = detect_institution_conflation(answer_text)
    suspicious_numbers = check_numeric_consistency(answer_text, chunks) if chunks else []
    has_suspicious_numbers = bool(suspicious_numbers)
    uncited_negative_conclusions = check_uncited_negative_conclusion(answer_text)
    has_uncited_negative = bool(uncited_negative_conclusions)
    return GuardResult(
        is_low_confidence=(
            is_low_confidence or has_ungrounded or has_conflation
            or has_no_citations or has_suspicious_numbers or has_uncited_negative
        ),
        best_rerank_score=best_score,
        citation_checks=citation_checks,
        suspicious_numbers=suspicious_numbers,
        uncited_negative_conclusions=uncited_negative_conclusions,
    )


def format_guard_warnings(result: GuardResult) -> str:
    """Kullaniciya gosterilecek uyari metnini uretir (varsa)."""
    warnings = []
    if result.is_low_confidence:
        warnings.append(
            "UYARI - DUSUK GUVEN: Bulunan kaynaklar bu soruyla zayif iliskili "
            "gorunuyor. Bu cevabi temkinli degerlendirin, resmi metni "
            "mutlaka kontrol edin."
        )
    ungrounded = [c for c in result.citation_checks if not c.grounded]
    if ungrounded:
        nums = ", ".join(f"[{c.citation_num}]" for c in ungrounded)
        warnings.append(
            f"UYARI - DOGRULANAMAYAN ALINTI: {nums} numarali referans(lar)in "
            "alintisi, gosterilen kaynak pasajda birebir bulunamadi. Bu "
            "kismi ozellikle resmi metinle karsilastirin."
        )
    if result.suspicious_numbers:
        nums = ", ".join(result.suspicious_numbers)
        warnings.append(
            f"UYARI - DOGRULANAMAYAN SAYI: cevapta gecen {nums} degeri/degerleri "
            "kaynak pasajlarda bulunamadi. Bu rakam(lar)i resmi metinle "
            "ayrica dogrulayin."
        )
    if result.uncited_negative_conclusions:
        warnings.append(
            "UYARI - DESTEKSIZ OLUMSUZ SONUC: cevapta bir yasak/imkansizlik "
            "sonucu var ama bunu destekleyen bir alinti referansi yok - "
            "bu, modelin kendi cikarimi olabilir. Resmi metni ayrica "
            "kontrol edin."
        )
    return "\n".join(warnings)
