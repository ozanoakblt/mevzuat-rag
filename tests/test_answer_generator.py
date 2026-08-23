import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.generation.answer_generator import _format_context, generate_answer

SAMPLE_CHUNKS = [
    {
        "doc_id": "kanun-6446",
        "madde_no": "6",
        "fikra_no": "1",
        "bent_no": None,
        "madde_baslik": "Bağlantı ve sistem kullanım anlaşmaları",
        "text": "OSB'ler TEİAŞ'a başvurur.",
    },
    {
        "doc_id": "kanun-6446",
        "madde_no": "7",
        "fikra_no": "11",
        "bent_no": "a",
        "madde_baslik": "Anlaşma gücü",
        "text": "Anlaşma gücü TEİAŞ tarafından belirlenir.",
    },
]


def test_format_context_numbers_sources_and_includes_location():
    context = _format_context(SAMPLE_CHUNKS, {"kanun-6446": "6446 Sayılı Kanun"})
    assert "[1] Kaynak: 6446 Sayılı Kanun — Madde 6, fıkra (1)" in context
    assert "[2] Kaynak: 6446 Sayılı Kanun — Madde 7, fıkra (11), bent a)" in context
    assert "OSB'ler TEİAŞ'a başvurur." in context


def test_format_context_falls_back_to_doc_id_without_titles():
    context = _format_context(SAMPLE_CHUNKS)
    assert "Kaynak: kanun-6446" in context


def test_generate_answer_no_chunks_returns_honest_message_without_calling_groq():
    with patch("src.generation.answer_generator.chat_completion_text") as mock_call:
        answer = generate_answer("soru", [])
        assert "bulunamadı" in answer.lower()
        mock_call.assert_not_called()


@patch("src.generation.answer_generator.chat_completion_text")
def test_generate_answer_passes_context_and_query_to_groq(mock_call):
    mock_call.return_value = "Test cevabı [1]."
    answer = generate_answer("OSB bağlantısı nasıl yapılır", SAMPLE_CHUNKS)

    assert answer == "Test cevabı [1]."
    call_args = mock_call.call_args
    system_prompt, user_prompt = call_args[0][0], call_args[0][1]
    assert "SADECE" in system_prompt  # kural 1: context dışına çıkma
    assert "OSB bağlantısı nasıl yapılır" in user_prompt
    assert "OSB'ler TEİAŞ'a başvurur." in user_prompt


@patch("src.generation.answer_generator.chat_completion_text")
def test_generate_answer_uses_doc_titles_in_prompt(mock_call):
    mock_call.return_value = "cevap"
    generate_answer(
        "soru", SAMPLE_CHUNKS, doc_titles={"kanun-6446": "6446 Sayılı Elektrik Piyasası Kanunu"}
    )
    user_prompt = mock_call.call_args[0][1]
    assert "6446 Sayılı Elektrik Piyasası Kanunu" in user_prompt
