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


def _normalize(text: str) -> str:
    """
    Karşılaştırma için: TÜM boşlukları kaldır (sadece tek boşluğa indirmek
    değil), küçük harfe çevir. Neden tüm boşluklar: kaynak PDF'lerde font
    kerning'i kelime ortasına kaçak boşluk sokabiliyor (ör. "işletilmesi"
    -> "işletil mesi" — Faz 2'de "MA DDE" olarak gördüğümüz sorunun aynısı).
    Bu, modelin doğru yazdığı bir alıntının, kaynaktaki tesadüfi bir yazım
    kusuru yüzünden yanlışlıkla "doğrulanamadı" olarak işaretlenmesini
    engeller. Bu yaklaşımın riski çok düşük: iki farklı kelimenin
    birleşip yanlışlıkla eşleşmesi için çok uzun ortak alt diziler
    gerekir, pratikte ihmal edilebilir.
    """
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


def run_guard(answer_text: str, chunks: list[dict]) -> GuardResult:
    is_low_confidence, best_score = check_confidence(chunks)
    citation_checks = verify_citations(answer_text, chunks)
    return GuardResult(
        is_low_confidence=is_low_confidence,
        best_rerank_score=best_score,
        citation_checks=citation_checks,
    )


def format_guard_warnings(result: GuardResult) -> str:
    """Kullanıcıya gösterilecek uyarı metnini üretir (varsa)."""
    warnings = []
    if result.is_low_confidence:
        warnings.append(
            "⚠️  DÜŞÜK GÜVEN: Bulunan kaynaklar bu soruyla zayıf ilişkili "
            "görünüyor. Bu cevabı temkinli değerlendirin, resmî metni "
            "mutlaka kontrol edin."
        )
    ungrounded = [c for c in result.citation_checks if not c.grounded]
    if ungrounded:
        nums = ", ".join(f"[{c.citation_num}]" for c in ungrounded)
        warnings.append(
            f"⚠️  DOĞRULANAMAYAN ALINTI: {nums} numaralı referans(lar)ın "
            "alıntısı, gösterilen kaynak pasajda birebir bulunamadı. Bu "
            "kısımları özellikle resmî metinle karşılaştırın."
        )
    return "\n".join(warnings)