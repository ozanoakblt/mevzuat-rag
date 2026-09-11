from pathlib import Path
p = Path("src/generation/citation_guard.py")
s = p.read_text(encoding="utf-8")

old = """_NUMBER_RE = re.compile(r\"\\d+(?:[.,]\\d+)?\")


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
    return suspicious"""

new = """_NUMBER_RE = re.compile(r\"\\d+(?:[.,]\\d+)?\")

_LAW_NUMBER_CONTEXT_RE = re.compile(r\"\\b(\\d+)\\s+sayılı\\b\", re.IGNORECASE)


def check_numeric_consistency(answer_text: str, chunks: list[dict]) -> list[str]:
    \"\"\"
    Cevap metnindeki sayisal degerlerin, kaynak pasajlarin herhangi
    birinde gecip gecmedigini kontrol eder. Tek/cift basamaksiz kucuk
    sayilar (0-9) VE \"<sayi> sayili <Kanun/Yonetmelik>\" kalibiyla gecen
    belge numaralari kontrol disi tutulur - ikincisi genelde chunk
    metninde degil doc_titles metadata'sinda (baslikta) tutulan bir
    BELGE KIMLIGIDIR, dogrulanmasi gereken olgusal bir deger degildir.
    \"\"\"
    combined_source = _normalize_turkish_numbers(
        \"\\n\".join(c[\"text\"] for c in chunks)
    )
    answer_numbers = set(_NUMBER_RE.findall(_normalize_turkish_numbers(answer_text)))
    law_reference_numbers = {
        m.group(1) for m in _LAW_NUMBER_CONTEXT_RE.finditer(answer_text)
    }

    suspicious = []
    for num in sorted(answer_numbers):
        if num in law_reference_numbers:
            continue
        bare_digits = num.replace(\".\", \"\").replace(\",\", \"\")
        if len(bare_digits) < 2:
            continue
        if num not in combined_source:
            suspicious.append(num)
    return suspicious"""

assert old in s, "check_numeric_consistency bulunamadi - dosyanin guncel halini gonder"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("Tamamlandi: kanun/yonetmelik numaralari kontrol disi tutuluyor.")
