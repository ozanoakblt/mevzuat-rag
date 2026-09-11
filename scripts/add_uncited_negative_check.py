import re
from pathlib import Path
p = Path("src/generation/citation_guard.py")
s = p.read_text(encoding="utf-8")

old = """@dataclass
class GuardResult:
    is_low_confidence: bool
    best_rerank_score: float | None
    citation_checks: list[CitationCheck] = field(default_factory=list)
    suspicious_numbers: list[str] = field(default_factory=list)

    @property
    def has_ungrounded_citations(self) -> bool:
        return any(not c.grounded for c in self.citation_checks)"""

new = """@dataclass
class GuardResult:
    is_low_confidence: bool
    best_rerank_score: float | None
    citation_checks: list[CitationCheck] = field(default_factory=list)
    suspicious_numbers: list[str] = field(default_factory=list)
    uncited_negative_conclusions: list[str] = field(default_factory=list)

    @property
    def has_ungrounded_citations(self) -> bool:
        return any(not c.grounded for c in self.citation_checks)"""

assert old in s
s = s.replace(old, new)

marker = "def extract_citation_quotes(answer_text: str) -> dict[int, str]:"
assert marker in s

negative_check_code = """_NEGATIVE_CONCLUSION_RE = re.compile(
    r"[^.!?\\n]*\\b(yapılamaz|yapilamaz|mümkün değildir|mumkun degildir|"
    r"yasaktır|yasaktir|izin verilmez|uygulanamaz|geçerli değildir|"
    r"gecerli degildir|sağlanmamaktadır|saglanmamaktadir|"
    r"imkan(?:sızdır|sizdir))[^.!?\\n]*[.!?]",
    re.IGNORECASE,
)
_CITATION_MARKER_IN_SENTENCE_RE = re.compile(r"\\[\\d+\\]")


def check_uncited_negative_conclusion(answer_text: str) -> list[str]:
    \"\"\"
    Cevap govdesinde (alinti blogu haric) yapilamaz/yasaktir/mumkun
    degildir gibi OLUMSUZ bir sonuc iceren ama icinde hicbir [N] alinti
    referansi OLMAYAN cumleleri tespit eder - modelin kendi mantiksal
    cikarimiyla urettigi bir yasak sonucu olabilecegini gosteren isaret.
    \"\"\"
    body = answer_text.split("Kaynak Alıntıları:")[0]
    suspicious = []
    for match in _NEGATIVE_CONCLUSION_RE.finditer(body):
        sentence = match.group(0)
        if not _CITATION_MARKER_IN_SENTENCE_RE.search(sentence):
            suspicious.append(sentence.strip())
    return suspicious


""" + marker

s = s.replace(marker, negative_check_code, 1)

old_guard = """    suspicious_numbers = check_numeric_consistency(answer_text, chunks) if chunks else []
    has_suspicious_numbers = bool(suspicious_numbers)
    return GuardResult(
        is_low_confidence=(
            is_low_confidence or has_ungrounded or has_conflation
            or has_no_citations or has_suspicious_numbers
        ),
        best_rerank_score=best_score,
        citation_checks=citation_checks,
        suspicious_numbers=suspicious_numbers,
    )"""
new_guard = """    suspicious_numbers = check_numeric_consistency(answer_text, chunks) if chunks else []
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
    )"""
assert old_guard in s
s = s.replace(old_guard, new_guard)

old_warn = """    if result.suspicious_numbers:
        nums = \", \".join(result.suspicious_numbers)
        warnings.append(
            f\"UYARI - DOGRULANAMAYAN SAYI: cevapta gecen {nums} degeri/degerleri \"
            \"kaynak pasajlarda bulunamadi. Bu rakam(lar)i resmi metinle \"
            \"ayrica dogrulayin.\"
        )
    return \"\\n\".join(warnings)"""
new_warn = """    if result.suspicious_numbers:
        nums = \", \".join(result.suspicious_numbers)
        warnings.append(
            f\"UYARI - DOGRULANAMAYAN SAYI: cevapta gecen {nums} degeri/degerleri \"
            \"kaynak pasajlarda bulunamadi. Bu rakam(lar)i resmi metinle \"
            \"ayrica dogrulayin.\"
        )
    if result.uncited_negative_conclusions:
        warnings.append(
            \"UYARI - DESTEKSIZ OLUMSUZ SONUC: cevapta bir yasak/imkansizlik \"
            \"sonucu var ama bunu destekleyen bir alinti referansi yok - \"
            \"bu, modelin kendi cikarimi olabilir. Resmi metni ayrica \"
            \"kontrol edin.\"
        )
    return \"\\n\".join(warnings)"""
assert old_warn in s
s = s.replace(old_warn, new_warn)

p.write_text(s, encoding="utf-8")
print("Tamamlandi.")
