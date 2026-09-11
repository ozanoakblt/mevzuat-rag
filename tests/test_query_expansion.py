"""
query_expansion modulu icin testler.
"""
from unittest.mock import patch

import pytest

import src.retrieval.query_expansion as query_expansion
from src.common.llm_router import LLMError
from src.retrieval.query_expansion import expand_query


class FakeEmbedder:
    def __init__(self, vectors):
        self.vectors = vectors
        self.call_count = 0

    def embed_query(self, text):
        self.call_count += 1
        if text not in self.vectors:
            raise KeyError(f"FakeEmbedder icin tanimsiz metin: {text!r}")
        return self.vectors[text]


@pytest.fixture(autouse=True)
def isolate_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(query_expansion, "_CACHE_PATH", tmp_path / "cache.json")
    monkeypatch.setattr(query_expansion, "_embedder_singleton", None)


def test_expand_query_returns_queries_from_groq():
    fake_response = {"queries": ["soru 1", "soru 2", "soru 3"]}
    with patch("src.retrieval.query_expansion.chat_completion_json", return_value=fake_response):
        result = expand_query("orijinal soru", embedder=FakeEmbedder({"orijinal soru": [1.0, 0.0]}))
    assert result == ["soru 1", "soru 2", "soru 3"]


def test_expand_query_falls_back_to_original_on_llm_error():
    with patch("src.retrieval.query_expansion.chat_completion_json", side_effect=LLMError("rate limit")):
        result = expand_query("orijinal soru", embedder=FakeEmbedder({"orijinal soru": [1.0, 0.0]}))
    assert result == ["orijinal soru"]


def test_expand_query_falls_back_when_queries_missing():
    with patch("src.retrieval.query_expansion.chat_completion_json", return_value={}):
        result = expand_query("orijinal soru", embedder=FakeEmbedder({"orijinal soru": [1.0, 0.0]}))
    assert result == ["orijinal soru"]


def test_expand_query_filters_empty_and_non_string_entries():
    fake_response = {"queries": ["gecerli soru", "", None, "   ", "baska soru"]}
    with patch("src.retrieval.query_expansion.chat_completion_json", return_value=fake_response):
        result = expand_query("orijinal soru", embedder=FakeEmbedder({"orijinal soru": [1.0, 0.0]}))
    assert result == ["gecerli soru", "baska soru"]


def test_expand_query_respects_max_queries():
    fake_response = {"queries": ["s1", "s2", "s3", "s4", "s5"]}
    with patch("src.retrieval.query_expansion.chat_completion_json", return_value=fake_response):
        result = expand_query("orijinal soru", max_queries=2, embedder=FakeEmbedder({"orijinal soru": [1.0, 0.0]}))
    assert result == ["s1", "s2"]


def test_expand_query_uses_exact_cache_on_second_call():
    fake_response = {"queries": ["soru 1", "soru 2", "soru 3"]}
    fake_embedder = FakeEmbedder({"tekrar sorulan soru": [1.0, 0.0]})
    with patch("src.retrieval.query_expansion.chat_completion_json", return_value=fake_response) as mock_llm:
        first = expand_query("tekrar sorulan soru", embedder=fake_embedder)
        second = expand_query("tekrar sorulan soru", embedder=fake_embedder)
    assert mock_llm.call_count == 1
    assert first == second == ["soru 1", "soru 2", "soru 3"]


def test_expand_query_does_not_cache_llm_error_fallback():
    with patch("src.retrieval.query_expansion.chat_completion_json", side_effect=LLMError("gecici hata")) as mock_llm:
        expand_query("hata sorusu", embedder=FakeEmbedder({"hata sorusu": [1.0, 0.0]}))
        expand_query("hata sorusu", embedder=FakeEmbedder({"hata sorusu": [1.0, 0.0]}))
    assert mock_llm.call_count == 2


def test_expand_query_semantic_match_reuses_cache_without_llm_call():
    fake_response = {"queries": ["s1", "s2", "s3"]}
    vectors = {
        "kesinti tazminati nasil hesaplanir": [1.0, 0.0],
        "kesinti tazminatinin hesaplanma yontemi nedir": [0.999, 0.045],
    }
    with patch("src.retrieval.query_expansion.chat_completion_json", return_value=fake_response) as mock_llm:
        first = expand_query("kesinti tazminati nasil hesaplanir", embedder=FakeEmbedder(vectors))
        second = expand_query("kesinti tazminatinin hesaplanma yontemi nedir", embedder=FakeEmbedder(vectors))
    assert mock_llm.call_count == 1
    assert first == second == ["s1", "s2", "s3"]


def test_expand_query_dissimilar_question_does_not_reuse_cache():
    fake_response_1 = {"queries": ["s1", "s2", "s3"]}
    fake_response_2 = {"queries": ["farkli1", "farkli2", "farkli3"]}
    vectors = {
        "kesinti tazminati nasil hesaplanir": [1.0, 0.0],
        "lisans basvurusu nasil yapilir": [0.1, 0.99],
    }
    with patch("src.retrieval.query_expansion.chat_completion_json", side_effect=[fake_response_1, fake_response_2]) as mock_llm:
        first = expand_query("kesinti tazminati nasil hesaplanir", embedder=FakeEmbedder(vectors))
        second = expand_query("lisans basvurusu nasil yapilir", embedder=FakeEmbedder(vectors))
    assert mock_llm.call_count == 2
    assert first == ["s1", "s2", "s3"]
    assert second == ["farkli1", "farkli2", "farkli3"]


def test_expand_query_backward_compatible_with_legacy_list_format():
    query_expansion._CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    key = query_expansion._cache_key("eski format sorusu")
    query_expansion._CACHE_PATH.write_text('{"' + key + '": ["eski1", "eski2"]}', encoding="utf-8")
    with patch("src.retrieval.query_expansion.chat_completion_json") as mock_llm:
        result = expand_query("eski format sorusu", embedder=FakeEmbedder({"eski format sorusu": [1.0, 0.0]}))
    assert result == ["eski1", "eski2"]
    mock_llm.assert_not_called()


def test_expand_query_embedder_failure_falls_back_to_llm():
    class BrokenEmbedder:
        def embed_query(self, text):
            raise RuntimeError("model yuklenemedi")

    fake_response = {"queries": ["s1", "s2", "s3"]}
    with patch("src.retrieval.query_expansion.chat_completion_json", return_value=fake_response):
        result = expand_query("herhangi bir soru", embedder=BrokenEmbedder())
    assert result == ["s1", "s2", "s3"]
