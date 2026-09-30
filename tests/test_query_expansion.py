"""
query_expansion modulu icin testler.
"""
import json
from unittest.mock import patch

import pytest

import src.retrieval.query_expansion as query_expansion
from src.common.llm_router import LLMError
from src.retrieval.query_expansion import expand_query, get_query_type


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


def test_expand_query_skips_cache_entries_with_null_embedding():
    # Gercek bir vakada tespit edildi: embedder o zamanki cagride basarisiz
    # olup query_embedding=None dondugunde, "embedding" anahtari kayitta
    # VAR ama degeri None oluyor. Benzerlik dongusu sadece anahtarin
    # varligini kontrol ediyordu, None degeri es geciyordu ve
    # _cosine_similarity(query_embedding, None) TypeError firlatip
    # /api/ask'i tamamen kirıyordu (500 Internal Server Error).
    query_expansion._CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    bad_key = query_expansion._cache_key("bozuk kayitli soru")
    bad_entry = {"question": "bozuk kayitli soru", "embedding": None, "queries": ["x"], "query_type": "genel_hukum"}
    query_expansion._CACHE_PATH.write_text(json.dumps({bad_key: bad_entry}), encoding="utf-8")

    fake_response = {"queries": ["yeni1", "yeni2"]}
    with patch("src.retrieval.query_expansion.chat_completion_json", return_value=fake_response):
        result = expand_query("tamamen farkli yeni bir soru", embedder=FakeEmbedder({"tamamen farkli yeni bir soru": [1.0, 0.0]}))
    assert result == ["yeni1", "yeni2"]


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


def test_expand_query_does_not_reuse_cache_for_different_dates_despite_high_similarity():
    # Gercek bir vakada tespit edildi: "X tarihli degisiklikle Y
    # Yonetmeliginde ne degisti?" kalibindaki iki soru, FARKLI tarihli iki
    # AYRI degisiklik hakkinda olsa bile 0.93 esiginin UZERINDE anlamsal
    # benzerlik verebiliyor - tarih iceren sorularda bu ayrimin gozden
    # kacmamasi gerekir.
    fake_response_1 = {"queries": ["25.06.2026 degisikligi hakkinda s1", "s2", "s3"]}
    fake_response_2 = {"queries": ["27.01.2026 degisikligi hakkinda s1", "s2", "s3"]}
    vectors = {
        "25.06.2026 tarihli degisiklikle Yonetmelikte ne degisti?": [1.0, 0.0],
        "27.01.2026 tarihli degisiklikle Yonetmelikte ne degisti?": [0.999, 0.045],
    }
    with patch(
        "src.retrieval.query_expansion.chat_completion_json",
        side_effect=[fake_response_1, fake_response_2],
    ) as mock_llm:
        first = expand_query("25.06.2026 tarihli degisiklikle Yonetmelikte ne degisti?", embedder=FakeEmbedder(vectors))
        second = expand_query("27.01.2026 tarihli degisiklikle Yonetmelikte ne degisti?", embedder=FakeEmbedder(vectors))
    assert mock_llm.call_count == 2
    assert first != second
    assert "25.06.2026" in first[0]
    assert "27.01.2026" in second[0]


def test_expand_query_embedder_failure_falls_back_to_llm():
    class BrokenEmbedder:
        def embed_query(self, text):
            raise RuntimeError("model yuklenemedi")

    fake_response = {"queries": ["s1", "s2", "s3"]}
    with patch("src.retrieval.query_expansion.chat_completion_json", return_value=fake_response):
        result = expand_query("herhangi bir soru", embedder=BrokenEmbedder())
    assert result == ["s1", "s2", "s3"]


def test_get_query_type_returns_classified_type():
    fake_response = {"queries": ["s1", "s2", "s3"], "query_type": "guncel_deger"}
    with patch("src.retrieval.query_expansion.chat_completion_json", return_value=fake_response):
        result = get_query_type(
            "2026 serbest tuketici limiti kac kWh?", embedder=FakeEmbedder({"2026 serbest tuketici limiti kac kWh?": [1.0, 0.0]})
        )
    assert result == "guncel_deger"


def test_get_query_type_defaults_to_genel_hukum_when_missing():
    fake_response = {"queries": ["s1", "s2", "s3"]}
    with patch("src.retrieval.query_expansion.chat_completion_json", return_value=fake_response):
        result = get_query_type("soru", embedder=FakeEmbedder({"soru": [1.0, 0.0]}))
    assert result == "genel_hukum"


def test_get_query_type_rejects_unknown_type_value():
    fake_response = {"queries": ["s1", "s2", "s3"], "query_type": "gecersiz_deger"}
    with patch("src.retrieval.query_expansion.chat_completion_json", return_value=fake_response):
        result = get_query_type("soru", embedder=FakeEmbedder({"soru": [1.0, 0.0]}))
    assert result == "genel_hukum"


def test_get_query_type_fails_open_on_llm_error():
    with patch(
        "src.retrieval.query_expansion.chat_completion_json", side_effect=LLMError("rate limit")
    ):
        result = get_query_type("soru", embedder=FakeEmbedder({"soru": [1.0, 0.0]}))
    assert result == "genel_hukum"


def test_expand_query_and_get_query_type_share_single_llm_call():
    # Maliyet kontrolu: ayni soru icin once expand_query, sonra get_query_type
    # cagrilirsa, ikinci cagri cache'ten okumali - TOPLAM 1 LLM cagrisi
    # olmali, 2 DEGIL (siniflandirma icin ayri bir cagri EKLENMEMELI).
    fake_response = {"queries": ["s1", "s2", "s3"], "query_type": "vaka"}
    embedder = FakeEmbedder({"paylasilan soru": [1.0, 0.0]})
    with patch(
        "src.retrieval.query_expansion.chat_completion_json", return_value=fake_response
    ) as mock_llm:
        queries = expand_query("paylasilan soru", embedder=embedder)
        qtype = get_query_type("paylasilan soru", embedder=embedder)

    assert mock_llm.call_count == 1
    assert queries == ["s1", "s2", "s3"]
    assert qtype == "vaka"
