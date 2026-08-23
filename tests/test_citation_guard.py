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
    {"text": "OSB'ler TEİAŞ'a başvurur ve bu Yönetmelik ile Elektrik Şebeke Yönetmeliğine göre incelenir.", "rerank_score": 2.5},
    {"text": "Anlaşma gücü TEİAŞ tarafından belirlenir.", "rerank_score": 1.2},
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

Kaynak Alıntıları:
[1]: "OSB'ler TEİAŞ'a başvurur"
[2]: "Anlaşma gücü TEİAŞ tarafından belirlenir"
'''
    quotes = extract_citation_quotes(answer)
    assert quotes[1] == "OSB'ler TEİAŞ'a başvurur"
    assert quotes[2] == "Anlaşma gücü TEİAŞ tarafından belirlenir"


def test_verify_citations_grounded_quote_passes():
    answer = 'Kaynak Alıntıları:\n[1]: "OSB\'ler TEİAŞ\'a başvurur"'
    checks = verify_citations(answer, CHUNKS)
    assert len(checks) == 1
    assert checks[0].grounded is True


def test_verify_citations_fabricated_quote_flagged():
    answer = 'Kaynak Alıntıları:\n[1]: "bu cümle kaynakta yok ve uydurulmuş"'
    checks = verify_citations(answer, CHUNKS)
    assert checks[0].grounded is False


def test_verify_citations_out_of_range_citation_flagged():
    answer = 'Kaynak Alıntıları:\n[5]: "olmayan referans"'
    checks = verify_citations(answer, CHUNKS)
    assert checks[0].grounded is False


def test_verify_citations_case_and_whitespace_insensitive():
    answer = 'Kaynak Alıntıları:\n[1]: "OSB\'LER   TEİAŞ\'a   başvurur"'
    checks = verify_citations(answer, CHUNKS)
    assert checks[0].grounded is True


def test_verify_citations_survives_pdf_kerning_artifact():
    """
    Gerçek bir vakadan: kaynak PDF'te "işletilmesi" kelimesi font kerning
    yüzünden "işletil mesi" olarak çıkarılmıştı (Faz 2'deki "MA DDE"
    hatasıyla aynı kategoriden). Model doğru yazımla alıntı yapınca eski
    kod bunu yanlışlıkla "doğrulanamadı" işaretliyordu — artık işaretlememeli.
    """
    kerning_chunks = [
        {
            "text": "sayaçlarının kurulumu, işletil mesi ve bakımı dağıtım şirketi tarafından yapılır.",
            "rerank_score": 1.0,
        }
    ]
    answer = 'Kaynak Alıntıları:\n[1]: "sayaçlarının kurulumu, işletilmesi ve bakımı dağıtım şirketi tarafından yapılır."'
    checks = verify_citations(answer, kerning_chunks)
    assert checks[0].grounded is True


def test_run_guard_combines_both_checks():
    answer = 'Kaynak Alıntıları:\n[1]: "OSB\'ler TEİAŞ\'a başvurur"'
    result = run_guard(answer, CHUNKS)
    assert result.is_low_confidence is False
    assert result.has_ungrounded_citations is False


def test_format_guard_warnings_empty_when_all_good():
    answer = 'Kaynak Alıntıları:\n[1]: "OSB\'ler TEİAŞ\'a başvurur"'
    result = run_guard(answer, CHUNKS)
    assert format_guard_warnings(result) == ""


def test_format_guard_warnings_flags_low_confidence():
    low_chunks = [{"text": "x", "rerank_score": -3.1}]
    result = run_guard("Kaynak Alıntıları:\n[1]: \"x\"", low_chunks)
    warnings = format_guard_warnings(result)
    assert "DÜŞÜK GÜVEN" in warnings


def test_format_guard_warnings_flags_ungrounded_citation():
    answer = 'Kaynak Alıntıları:\n[1]: "uydurulmuş bir alıntı"'
    result = run_guard(answer, CHUNKS)
    warnings = format_guard_warnings(result)
    assert "DOĞRULANAMAYAN ALINTI" in warnings
    assert "[1]" in warnings