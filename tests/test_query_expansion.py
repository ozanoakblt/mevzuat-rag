"""
query_expansion modulu icin testler.
"""
from unittest.mock import patch

from src.retrieval.query_expansion import expand_query
from src.common.groq_client import GroqError


def test_expand_query_returns_queries_from_groq():
    fake_response = {"queries": ["soru 1", "soru 2", "soru 3"]}
    with patch(
        "src.retrieval.query_expansion.chat_completion_json",
        return_value=fake_response,
    ):
        result = expand_query("orijinal soru")
    assert result == ["soru 1", "soru 2", "soru 3"]


def test_expand_query_falls_back_to_original_on_groq_error():
    with patch(
        "src.retrieval.query_expansion.chat_completion_json",
        side_effect=GroqError("rate limit"),
    ):
        result = expand_query("orijinal soru")
    assert result == ["orijinal soru"]


def test_expand_query_falls_back_when_queries_missing():
    with patch(
        "src.retrieval.query_expansion.chat_completion_json",
        return_value={},
    ):
        result = expand_query("orijinal soru")
    assert result == ["orijinal soru"]


def test_expand_query_filters_empty_and_non_string_entries():
    fake_response = {"queries": ["gecerli soru", "", None, "   ", "baska soru"]}
    with patch(
        "src.retrieval.query_expansion.chat_completion_json",
        return_value=fake_response,
    ):
        result = expand_query("orijinal soru")
    assert result == ["gecerli soru", "baska soru"]


def test_expand_query_respects_max_queries():
    fake_response = {"queries": ["s1", "s2", "s3", "s4", "s5"]}
    with patch(
        "src.retrieval.query_expansion.chat_completion_json",
        return_value=fake_response,
    ):
        result = expand_query("orijinal soru", max_queries=2)
    assert result == ["s1", "s2"]
