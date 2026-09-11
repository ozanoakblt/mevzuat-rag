import re
from pathlib import Path

p = Path("src/generation/citation_guard.py")
s = p.read_text(encoding="utf-8")

pattern = re.compile(r"_NUMBER_RE = re\.compile.*?\n\n\ndef extract_citation_quotes", re.DOTALL)

new_block = """_NUMBER_RE = re.compile(r"\\d+(?:[.,]\\d+)?")

_LAW_NUMBER_CONTEXT_RE = re.compile(r"\\b(\\d+)\\s+sayılı\\b", re.IGNORECASE)

_ARTICLE_NUMBER_CONTEXT_RE = re.compile(
    r"\\b(?:madde|fıkra|bent)\\s*\\(?(\\d+)\\)?\\b"
    r"|\\b(\\d+)\\s*(?:inci|ıncı|ncı|nci|uncu|üncü)?\\s+(?:madde|fıkra|bent)\\w*\\b",
    re.IGNORECASE,
)

_DATE_RE = re.compile(r"\\b\\d{1,2}[./]\\d{1,2}[./]\\d{2,4}\\b")


def check_numeric_consistency(answer_text: str, chunks: list[dict]) -> list[str]:
    \"\"\"
    Cevap metnindeki sayisal degerlerin, kaynak pasajlarin herhangi
    birinde gecip gecmedigini kontrol eder. Su durumlar kontrol disi
    tutulur:
    - Tek/cift basamaksiz kucuk sayilar (0-9)
    - "<sayi> sayili <Kanun/Yonetmelik>" (kanun numarasi)
    - "Madde <sayi>" / "<sayi> uncu madde" / "fikra (<sayi>)" (madde/fikra/
      bent numarasi)
    - Tarihler (27.01.2026, 5/6/2023 gibi)
    \"\"\"
    combined_source = _normalize_turkish_numbers(
        "\\n".join(c["text"] for c in chunks)
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


def extract_citation_quotes"""

s_new, count = pattern.subn(lambda m: new_block, s)
assert count == 1, f"beklenen 1 eslesme, {count} bulundu - dosyanin guncel halini gonder"
p.write_text(s_new, encoding="utf-8")
print("Tamamlandi: madde/fikra numaralari ve tarihler kontrol disi tutuluyor.")
