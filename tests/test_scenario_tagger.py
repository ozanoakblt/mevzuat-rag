import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.common.groq_client import GroqError
from src.tagging.scenario_tagger import classify_madde_text


@patch("src.tagging.scenario_tagger.chat_completion_json")
def test_valid_tags_kept(mock_call):
    mock_call.return_value = {"tags": ["baglanti_talebi", "gecici_baglanti"]}
    result = classify_madde_text("Şantiye için geçici bağlantı talebi...")
    assert result == ["baglanti_talebi", "gecici_baglanti"]


@patch("src.tagging.scenario_tagger.chat_completion_json")
def test_invalid_tags_dropped_hallucination_guard(mock_call):
    mock_call.return_value = {"tags": ["baglanti_talebi", "uydurma_kategori"]}
    result = classify_madde_text("Bir metin.")
    assert result == ["baglanti_talebi"]
    assert "uydurma_kategori" not in result


@patch("src.tagging.scenario_tagger.chat_completion_json")
def test_more_than_three_tags_truncated(mock_call):
    mock_call.return_value = {
        "tags": [
            "baglanti_talebi",
            "osb_baglantisi",
            "topraklama_izolasyon",
            "kesinti_tazminat",
        ]
    }
    result = classify_madde_text("Bir metin.")
    assert len(result) == 3


@patch("src.tagging.scenario_tagger.chat_completion_json")
def test_groq_error_returns_empty_list_no_guessing(mock_call):
    mock_call.side_effect = GroqError("API key yok")
    result = classify_madde_text("Bir metin.")
    assert result == []


def test_empty_text_skips_api_call():
    with patch("src.tagging.scenario_tagger.chat_completion_json") as mock_call:
        result = classify_madde_text("   ")
        assert result == []
        mock_call.assert_not_called()
