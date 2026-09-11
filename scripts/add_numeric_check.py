from pathlib import Path
p = Path("src/generation/citation_guard.py")
s = p.read_text(encoding="utf-8")

old = """@dataclass
class GuardResult:
    is_low_confidence: bool
    best_rerank_score: float | None
    citation_checks: list[CitationCheck] = field(default_factory=list)

    @property
    def has_ungrounded_citations(self) -> bool:
        return any(not c.grounded for c in self.citation_checks)"""
new = """@dataclass
class GuardResult:
    is_low_confidence: bool
    best_rerank_score: float | None
    citation_checks: list[CitationCheck] = field(default_factory=list)
    suspicious_numbers: list[str] = field(default_factory=list)

    @property
    def has_ungrounded_citations(self) -> bool:
        return any(not c.grounded for c in self.citation_checks)"""
assert old in s
s = s.replace(old, new)

old2 = """def extract_citation_quotes(answer_text: str) -> dict[int, str]:"""
new2 = """_NUMBER_RE = re.compile(r\"\\d+(?:[.,]\\d+)?\")


def check_numeric_consistency(answer_text: str, chunks: list[dict]) -> list[str]:
    \"\"\"
    Cevap metnindeki sayisal degerlerin, kaynak pasajlarin herhangi
    birinde gecip gecmedigini kontrol eder. Tek/cift basamaksiz kucuk
    sayilar (0-9) kontrol disi tutulur - madde/fikra/alinti referans
    numaralari olabilir, anlamli sinyal tasimazlar.
    \"\"\"
    combined_source = _normalize_turkish_numbers(
        \"\\n\".join(c[\"text\"] for c in chunks)
    )
    answer_numbers = set(_NUMBER_RE.findall(_normalize_turkish_numbers(answer_text)))

    suspicious = []
    for num in sorted(answer_numbers):
        bare_digits = num.replace(\".\", \"\").replace(\",\", \"\")
        if len(bare_digits) < 2:
            continue
        if num not in combined_source:
            suspicious.append(num)
    return suspicious


def extract_citation_quotes(answer_text: str) -> dict[int, str]:"""
assert old2 in s
s = s.replace(old2, new2)

old3 = """    has_no_citations = bool(chunks) and not citation_checks
    has_ungrounded = any(not c.grounded for c in citation_checks)
    has_conflation = detect_institution_conflation(answer_text)
    return GuardResult(
        is_low_confidence=is_low_confidence or has_ungrounded or has_conflation or has_no_citations,
        best_rerank_score=best_score,
        citation_checks=citation_checks,
    )"""
new3 = """    has_no_citations = bool(chunks) and not citation_checks
    has_ungrounded = any(not c.grounded for c in citation_checks)
    has_conflation = detect_institution_conflation(answer_text)
    suspicious_numbers = check_numeric_consistency(answer_text, chunks) if chunks else []
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
assert old3 in s
s = s.replace(old3, new3)

old4 = """    ungrounded = [c for c in result.citation_checks if not c.grounded]
    if ungrounded:
        nums = \", \".join(f\"[{c.citation_num}]\" for c in ungrounded)
        warnings.append(
            f\"UYARI - DOGRULANAMAYAN ALINTI: {nums} numarali referans(lar)in \"
            \"alintisi, gosterilen kaynak pasajda birebir bulunamadi. Bu \"
            \"kismi ozellikle resmi metinle karsilastirin.\"
        )
    return \"\\n\".join(warnings)"""
new4 = """    ungrounded = [c for c in result.citation_checks if not c.grounded]
    if ungrounded:
        nums = \", \".join(f\"[{c.citation_num}]\" for c in ungrounded)
        warnings.append(
            f\"UYARI - DOGRULANAMAYAN ALINTI: {nums} numarali referans(lar)in \"
            \"alintisi, gosterilen kaynak pasajda birebir bulunamadi. Bu \"
            \"kismi ozellikle resmi metinle karsilastirin.\"
        )
    if result.suspicious_numbers:
        nums = \", \".join(result.suspicious_numbers)
        warnings.append(
            f\"UYARI - DOGRULANAMAYAN SAYI: cevapta gecen {nums} degeri/degerleri \"
            \"kaynak pasajlarda bulunamadi. Bu rakam(lar)i resmi metinle \"
            \"ayrica dogrulayin.\"
        )
    return \"\\n\".join(warnings)"""
assert old4 in s
s = s.replace(old4, new4)

p.write_text(s, encoding="utf-8")
print("Tamamlandi.")
