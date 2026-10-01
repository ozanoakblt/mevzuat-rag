import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.common.llm_router import LLMError
from src.generation.claim_verifier import verify_claims

CHUNKS = [
    {"text": "Başvuru 7 iş günü içinde değerlendirilir."},
    {"text": "Anlaşma gücü TEİAŞ tarafından belirlenir."},
]


def test_verify_claims_returns_supported_claims():
    fake_response = {
        "claims": [
            {"text": "Başvuru 7 iş günü içinde değerlendirilir.", "citation_refs": [1], "supported": True, "reason": "Kaynakla birebir uyumlu."}
        ]
    }
    with patch("src.generation.claim_verifier.chat_completion_json", return_value=fake_response) as mock_llm:
        result = verify_claims("Başvuru 7 iş günü içinde değerlendirilir [1].", CHUNKS)

    mock_llm.assert_called_once()
    assert result.checked is True
    assert len(result.claims) == 1
    assert result.claims[0].supported is True
    assert result.has_unsupported_claims is False


def test_verify_claims_flags_overstated_claim():
    # Gercek vakadan (ChatGPT review): kaynak "degerlendirilir" (surec)
    # derken iddia "kesin olarak kabul edilir" (sonuc) diyorsa, alinti
    # birebir dogru olsa bile bu bir carpitmadir.
    fake_response = {
        "claims": [
            {
                "text": "Başvurunun kesin olarak kabul edilmesi 7 iş günü içinde tamamlanır.",
                "citation_refs": [1],
                "supported": False,
                "reason": "Kaynak sadece 'değerlendirilir' diyor, 'kabul edilir' demiyor - sonucu kesinleştiriyor.",
            }
        ]
    }
    with patch("src.generation.claim_verifier.chat_completion_json", return_value=fake_response):
        result = verify_claims(
            "Başvurunun kesin olarak kabul edilmesi 7 iş günü içinde tamamlanır [1].", CHUNKS
        )

    assert result.has_unsupported_claims is True
    assert result.unsupported_claims[0].citation_refs == [1]


def test_verify_claims_strips_kaynak_alintilari_section_from_body():
    with patch("src.generation.claim_verifier.chat_completion_json", return_value={"claims": []}) as mock_llm:
        verify_claims(
            'Cevap govdesi [1].\n\nKaynak Alıntıları:\n[1]: "Başvuru 7 iş günü içinde değerlendirilir."',
            CHUNKS,
        )

    user_prompt = mock_llm.call_args[0][1]
    assert "Cevap govdesi" in user_prompt
    assert 'Kaynak Alıntıları:\n[1]:' not in user_prompt


def test_verify_claims_returns_unchecked_when_no_chunks():
    result = verify_claims("Bu konuda kaynak bulunamadı.", [])
    assert result.checked is False
    assert result.claims == []


def test_verify_claims_returns_unchecked_when_body_empty():
    result = verify_claims("", CHUNKS)
    assert result.checked is False


def test_verify_claims_unchecked_not_treated_as_supported_on_llm_error():
    # applicability_checker'da duzeltilen fail-open hatasinin AYNISINI
    # burada en bastan yapmiyoruz: LLM hata verirse checked=False, claims
    # bos - "desteklendi" ile "kontrol edilemedi" KARISTIRILMAZ.
    with patch("src.generation.claim_verifier.chat_completion_json", side_effect=LLMError("rate limit")):
        result = verify_claims("Cevap govdesi [1].", CHUNKS)

    assert result.checked is False
    assert result.claims == []
    assert result.has_unsupported_claims is False  # bos liste, iddia yok demek


def test_verify_claims_ignores_malformed_claim_entries():
    fake_response = {"claims": [{"text": "iyi claim", "citation_refs": [1], "supported": True}, "bozuk-string-eleman", None]}
    with patch("src.generation.claim_verifier.chat_completion_json", return_value=fake_response):
        result = verify_claims("Cevap [1].", CHUNKS)

    assert len(result.claims) == 1
    assert result.claims[0].text == "iyi claim"
