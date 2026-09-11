from pathlib import Path
p = Path("tests/test_citation_guard.py")
s = p.read_text(encoding="utf-8")

old = """from src.generation.citation_guard import (
    check_confidence,
    extract_citation_quotes,
    format_guard_warnings,
    run_guard,
    verify_citations,
)"""
new = """from src.generation.citation_guard import (
    check_confidence,
    check_numeric_consistency,
    extract_citation_quotes,
    format_guard_warnings,
    run_guard,
    verify_citations,
)"""
assert old in s
s = s.replace(old, new)

s += \"\"\"

def test_check_numeric_consistency_passes_when_number_in_source():
    chunks = [{\"text\": \"Basvuru 90 gun icinde sonuclandirilir.\", \"rerank_score\": 1.0}]
    result = check_numeric_consistency(\"Basvuru sureci 90 gun surer.\", chunks)
    assert result == []


def test_check_numeric_consistency_flags_number_not_in_source():
    chunks = [{\"text\": \"Basvuru 90 gun icinde sonuclandirilir.\", \"rerank_score\": 1.0}]
    result = check_numeric_consistency(\"Basvuru sureci 45 gun surer.\", chunks)
    assert \"45\" in result
    assert \"90\" not in result


def test_check_numeric_consistency_ignores_single_digit_numbers():
    chunks = [{\"text\": \"Madde 5 uygulanir.\", \"rerank_score\": 1.0}]
    result = check_numeric_consistency(\"Bu konu Madde 7 kapsamindadir.\", chunks)
    assert result == []


def test_check_numeric_consistency_handles_turkish_number_words():
    chunks = [{\"text\": \"Sure doksan gun olarak belirlenmistir.\", \"rerank_score\": 1.0}]
    result = check_numeric_consistency(\"Sure 90 gundur.\", chunks)
    assert result == []


def test_run_guard_flags_suspicious_number_as_low_confidence():
    chunks = [{\"text\": \"Basvuru 90 gun icinde sonuclandirilir.\", \"rerank_score\": 2.0}]
    answer = 'Basvuru 45 gun icinde sonuclanir.\\nKaynak Alintilari:\\n[1]: \"Basvuru 90 gun icinde sonuclandirilir.\"'
    result = run_guard(answer, chunks)
    assert result.is_low_confidence is True
    assert \"45\" in result.suspicious_numbers


def test_format_guard_warnings_flags_suspicious_number():
    chunks = [{\"text\": \"Basvuru 90 gun icinde sonuclandirilir.\", \"rerank_score\": 2.0}]
    answer = 'Basvuru 45 gun icinde sonuclanir.\\nKaynak Alintilari:\\n[1]: \"Basvuru 90 gun icinde sonuclandirilir.\"'
    result = run_guard(answer, chunks)
    warnings = format_guard_warnings(result)
    assert \"DOGRULANAMAYAN SAYI\" in warnings
    assert \"45\" in warnings
\"\"\"

p.write_text(s, encoding="utf-8")
print("Tamamlandi.")
