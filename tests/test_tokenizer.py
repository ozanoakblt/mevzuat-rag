"""
tokenizer.py icin testler.
"""
from src.retrieval.tokenizer import turkish_lower, turkish_tokenize


def test_turkish_lower_handles_dotted_dotless_i():
    assert turkish_lower("İletim") == "iletim"
    assert turkish_lower("Iletim") == "ıletim"


def test_turkish_tokenize_filters_stopwords_and_short_tokens():
    tokens = turkish_tokenize("Bu bir madde ve fıkra ile ilgilidir")
    assert "bu" not in tokens
    assert "bir" not in tokens
    assert "ve" not in tokens
    assert "ile" not in tokens
    assert "madde" in tokens
    assert "fıkra" in tokens


def test_synonym_bridge_maps_setpoint_variants_to_common_token():
    setpoint_tokens = turkish_tokenize("Pset degeri setpoint olarak ayarlanir")
    set_point_tokens = turkish_tokenize("set point degeri nasil ayarlanir")
    assert "pset" in setpoint_tokens
    assert "pset" in set_point_tokens


def test_synonym_bridge_maps_azami_sinir_limit_to_common_token():
    azami_tokens = turkish_tokenize("azami guc degeri asilamaz")
    sinir_tokens = turkish_tokenize("sınır deger asilamaz")
    assert "limit" in azami_tokens
    assert "limit" in sinir_tokens


def test_synonym_bridge_does_not_affect_unrelated_tokens():
    tokens = turkish_tokenize("dagitim sirketi lisans basvurusu")
    assert "pset" not in tokens
    assert "limit" not in tokens
