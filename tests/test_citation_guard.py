import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.generation.citation_guard import (
    check_confidence,
    extract_citation_quotes,
    format_guard_warnings,
    run_guard,
    verify_citations,
)

CHUNKS = [
    {"text": "OSB'ler TEÄ°AÅ'a baÅŸvurur ve bu YÃ¶netmelik ile Elektrik Åebeke YÃ¶netmeliÄŸine gÃ¶re incelenir.", "rerank_score": 2.5},
    {"text": "AnlaÅŸma gÃ¼cÃ¼ TEÄ°AÅ tarafÄ±ndan belirlenir.", "rerank_score": 1.2},
]


def test_check_confidence_high_when_best_score_above_threshold():
    is_low, best = check_confidence(CHUNKS)
    assert is_low is False
    assert best == 2.5


def test_check_confidence_low_when_all_scores_negative():
    low_chunks = [{"text": "x", "rerank_score": -3.1}, {"text": "y", "rerank_score": -3.5}]
    is_low, best = check_confidence(low_chunks)
    assert is_low is True
    assert best == -3.1


def test_check_confidence_low_when_no_scores_present():
    is_low, best = check_confidence([{"text": "x"}])
    assert is_low is True
    assert best is None


def test_extract_citation_quotes_parses_format():
    answer = '''Cevap metni [1].

Kaynak AlÄ±ntÄ±larÄ±:
[1]: "OSB'ler TEÄ°AÅ'a baÅŸvurur"
[2]: "AnlaÅŸma gÃ¼cÃ¼ TEÄ°AÅ tarafÄ±ndan belirlenir"
'''
    quotes = extract_citation_quotes(answer)
    assert quotes[1] == "OSB'ler TEÄ°AÅ'a baÅŸvurur"
    assert quotes[2] == "AnlaÅŸma gÃ¼cÃ¼ TEÄ°AÅ tarafÄ±ndan belirlenir"


def test_verify_citations_grounded_quote_passes():
    answer = 'Kaynak AlÄ±ntÄ±larÄ±:\n[1]: "OSB\'ler TEÄ°AÅ\'a baÅŸvurur"'
    checks = verify_citations(answer, CHUNKS)
    assert len(checks) == 1
    assert checks[0].grounded is True


def test_verify_citations_fabricated_quote_flagged():
    answer = 'Kaynak AlÄ±ntÄ±larÄ±:\n[1]: "bu cÃ¼mle kaynakta yok ve uydurulmuÅŸ"'
    checks = verify_citations(answer, CHUNKS)
    assert checks[0].grounded is False


def test_verify_citations_out_of_range_citation_flagged():
    answer = 'Kaynak AlÄ±ntÄ±larÄ±:\n[5]: "olmayan referans"'
    checks = verify_citations(answer, CHUNKS)
    assert checks[0].grounded is False


def test_verify_citations_case_and_whitespace_insensitive():
    answer = 'Kaynak AlÄ±ntÄ±larÄ±:\n[1]: "OSB\'LER   TEÄ°AÅ\'a   baÅŸvurur"'
    checks = verify_citations(answer, CHUNKS)
    assert checks[0].grounded is True


def test_verify_citations_survives_pdf_kerning_artifact():
    """
    GerÃ§ek bir vakadan: kaynak PDF'te "iÅŸletilmesi" kelimesi font kerning
    yÃ¼zÃ¼nden "iÅŸletil mesi" olarak Ã§Ä±karÄ±lmÄ±ÅŸtÄ± (Faz 2'deki "MA DDE"
    hatasÄ±yla aynÄ± kategoriden). Model doÄŸru yazÄ±mla alÄ±ntÄ± yapÄ±nca eski
    kod bunu yanlÄ±ÅŸlÄ±kla "doÄŸrulanamadÄ±" iÅŸaretliyordu â€” artÄ±k iÅŸaretlememeli.
    """
    kerning_chunks = [
        {
            "text": "sayaÃ§larÄ±nÄ±n kurulumu, iÅŸletil mesi ve bakÄ±mÄ± daÄŸÄ±tÄ±m ÅŸirketi tarafÄ±ndan yapÄ±lÄ±r.",
            "rerank_score": 1.0,
        }
    ]
    answer = 'Kaynak AlÄ±ntÄ±larÄ±:\n[1]: "sayaÃ§larÄ±nÄ±n kurulumu, iÅŸletilmesi ve bakÄ±mÄ± daÄŸÄ±tÄ±m ÅŸirketi tarafÄ±ndan yapÄ±lÄ±r."'
    checks = verify_citations(answer, kerning_chunks)
    assert checks[0].grounded is True


def test_run_guard_combines_both_checks():
    answer = 'Kaynak AlÄ±ntÄ±larÄ±:\n[1]: "OSB\'ler TEÄ°AÅ\'a baÅŸvurur"'
    result = run_guard(answer, CHUNKS)
    assert result.is_low_confidence is False
    assert result.has_ungrounded_citations is False


def test_format_guard_warnings_empty_when_all_good():
    answer = 'Kaynak AlÄ±ntÄ±larÄ±:\n[1]: "OSB\'ler TEÄ°AÅ\'a baÅŸvurur"'
    result = run_guard(answer, CHUNKS)
    assert format_guard_warnings(result) == ""


def test_format_guard_warnings_flags_low_confidence():
    low_chunks = [{"text": "x", "rerank_score": -3.1}]
    result = run_guard("Kaynak AlÄ±ntÄ±larÄ±:\n[1]: \"x\"", low_chunks)
    warnings = format_guard_warnings(result)
    assert "DUSUK GUVEN" in warnings


def test_format_guard_warnings_flags_ungrounded_citation():
    answer = 'Kaynak AlÄ±ntÄ±larÄ±:\n[1]: "uydurulmuÅŸ bir alÄ±ntÄ±"'
    result = run_guard(answer, CHUNKS)
    warnings = format_guard_warnings(result)
    assert "DOGRULANAMAYAN ALINTI" in warnings
    assert "[1]" in warnings
