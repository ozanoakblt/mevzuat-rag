from pathlib import Path
p = Path("tests/test_citation_guard.py")
s = p.read_text(encoding="utf-8")

old = """from src.generation.citation_guard import (
    check_confidence,
    check_numeric_consistency,
    extract_citation_quotes,
    format_guard_warnings,
    run_guard,
    verify_citations,
)"""
new = """from src.generation.citation_guard import (
    check_confidence,
    check_numeric_consistency,
    check_uncited_negative_conclusion,
    extract_citation_quotes,
    format_guard_warnings,
    run_guard,
    verify_citations,
)"""
assert old in s
s = s.replace(old, new)

s += """

def test_check_uncited_negative_conclusion_flags_unsupported_prohibition():
    text = "Dolayısıyla, şaltı hazır ama iletim hattı henüz tesis edilmemişse, geçici kabul yapılamaz."
    result = check_uncited_negative_conclusion(text)
    assert len(result) == 1


def test_check_uncited_negative_conclusion_ignores_honest_refusal():
    text = 'Kaynaklar bu konuyu duzenlemiyor [1], [2]. Dolayısıyla bu konular için mevzuatta doğrudan bir hüküm bulunmamaktadır.'
    result = check_uncited_negative_conclusion(text)
    assert result == []


def test_check_uncited_negative_conclusion_ignores_cited_prohibition():
    text = "Kaynağa göre bu durumda hizmet sağlanamaz [3]."
    result = check_uncited_negative_conclusion(text)
    assert result == []


def test_run_guard_flags_uncited_negative_conclusion_as_low_confidence():
    chunks = [{"text": "Bağlantı hattı tesis edildiğinde geçici kabul yapılır.", "rerank_score": 2.0}]
    answer = 'Bağlantı hattı tesis edildiğinde geçici kabul yapılır [1].\\nDolayısıyla hat yoksa geçici kabul yapılamaz.\\nKaynak Alıntıları:\\n[1]: "Bağlantı hattı tesis edildiğinde geçici kabul yapılır."'
    result = run_guard(answer, chunks)
    assert result.is_low_confidence is True
    assert len(result.uncited_negative_conclusions) == 1


def test_format_guard_warnings_flags_uncited_negative_conclusion():
    chunks = [{"text": "Bağlantı hattı tesis edildiğinde geçici kabul yapılır.", "rerank_score": 2.0}]
    answer = 'Bağlantı hattı tesis edildiğinde geçici kabul yapılır [1].\\nDolayısıyla hat yoksa geçici kabul yapılamaz.\\nKaynak Alıntıları:\\n[1]: "Bağlantı hattı tesis edildiğinde geçici kabul yapılır."'
    result = run_guard(answer, chunks)
    warnings = format_guard_warnings(result)
    assert "DESTEKSIZ OLUMSUZ SONUC" in warnings
"""

p.write_text(s, encoding="utf-8")
print("Tamamlandi.")
