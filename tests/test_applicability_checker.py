import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.common.llm_router import LLMError
from src.generation.applicability_checker import check_applicability


def test_check_applicability_returns_true_when_llm_confirms_match():
    fake_response = {"applicable": True, "reason": "Hukum dogrudan bu duruma uygulaniyor."}
    with patch(
        "src.generation.applicability_checker.chat_completion_json", return_value=fake_response
    ) as mock_llm:
        result = check_applicability("Kesinti suresi kac gundur?", "Cevap [1].")

    mock_llm.assert_called_once()
    assert result.applicable is True
    assert result.checked is True
    assert "uygulaniyor" in result.reason


def test_check_applicability_flags_mismatched_scenario():
    # Gercek bir vakadan (Soru 40): soru "kullanici kaynakli DEGIL" diyor
    # ama cevap "kullanici kaynakli bozulma" hukmunu kullaniyor - LLM
    # bunu bir uyumsuzluk olarak isaretlemeli.
    fake_response = {
        "applicable": False,
        "reason": "Soru kullanici kaynakli olmayan bir ariza tarif ediyor ama cevap kullanici kaynakli bozulma hukumlerini uyguluyor.",
    }
    with patch(
        "src.generation.applicability_checker.chat_completion_json", return_value=fake_response
    ):
        result = check_applicability(
            "OG bagli kullanici sikayet etti, ariza kullanici kaynakli degil, ne yapilir?",
            "Kullanici kaynakli bozulmayi 90/180 gun icinde gidermelidir [1].",
        )

    assert result.applicable is False
    assert result.checked is True
    assert "uyumsuz" in result.reason.lower() or "kullanici kaynakli" in result.reason.lower()


def test_check_applicability_returns_unknown_not_safe_on_llm_error():
    # LLM basarisiz olursa (kota/hata) guard'i BLOKLAMAMALI ama "kontrol
    # edildi, sorun yok" da DEMEMELI - applicable=None, checked=False
    # donmeli. Eskiden applicable=True donuyordu (fail-open); bu,
    # "kontrol basarisiz oldu" ile "kontrol edildi ve uygun" arasindaki
    # farki gizleyip yanlis guvenlik sinyali veriyordu.
    with patch(
        "src.generation.applicability_checker.chat_completion_json",
        side_effect=LLMError("rate limit"),
    ):
        result = check_applicability("soru", "cevap")

    assert result.applicable is None
    assert result.checked is False


def test_check_applicability_sends_retrieved_chunk_text_to_llm():
    # Checker eskiden sadece (question, answer) goruyordu - cevabin
    # dogrulugunu yine cevabin kendisine bakarak yargiliyordu. Artik
    # kullanilan ham kaynak pasajlar da prompta ekleniyor.
    fake_response = {"applicable": True, "reason": "ok"}
    chunks = [{"madde_kind": "MADDE", "madde_no": "10", "text": "ham kaynak pasaj metni XYZ"}]
    with patch(
        "src.generation.applicability_checker.chat_completion_json", return_value=fake_response
    ) as mock_llm:
        check_applicability("soru", "cevap", retrieved_chunks=chunks)

    user_prompt = mock_llm.call_args[0][1]
    assert "ham kaynak pasaj metni XYZ" in user_prompt


def test_check_applicability_defaults_to_true_when_field_missing():
    with patch(
        "src.generation.applicability_checker.chat_completion_json", return_value={}
    ):
        result = check_applicability("soru", "cevap")

    assert result.applicable is True
    assert result.checked is True


def test_check_applicability_sends_question_and_answer_to_llm():
    fake_response = {"applicable": True, "reason": "ok"}
    with patch(
        "src.generation.applicability_checker.chat_completion_json", return_value=fake_response
    ) as mock_llm:
        check_applicability("test sorusu XYZ", "test cevabi ABC")

    user_prompt = mock_llm.call_args[0][1]
    assert "test sorusu XYZ" in user_prompt
    assert "test cevabi ABC" in user_prompt
