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


def test_madde_reference_becomes_distinct_token():
    # "EK MADDE 5" ile "MADDE 5" ayirt edilebilmeli (madde numarasi catismasi).
    assert "ek_madde_5" in turkish_tokenize("EK MADDE 5 hakkinda")
    assert "ek_madde_5" not in turkish_tokenize("MADDE 5 hakkinda")
    assert "madde_5" in turkish_tokenize("MADDE 5 hakkinda")


def test_madde_reference_with_letter_suffix_is_kept_whole():
    # Eskiden "5/A" -> "5" (tek haneli) ve "a" (tek karakter) diye kayboluyordu.
    tokens = turkish_tokenize("MADDE 5/A uyarinca")
    assert "madde_5/a" in tokens
    assert "5/a" in tokens


def test_gecici_madde_reference_uses_turkish_safe_lowercasing():
    assert "geçici_madde_4" in turkish_tokenize("GEÇİCİ MADDE 4")


def test_dates_are_normalized_to_single_token_in_any_separator():
    assert "27.01.2026" in turkish_tokenize("27.01.2026 tarihli")
    assert "27.01.2026" in turkish_tokenize("27/1/2026 tarihli")


def test_legal_tokens_are_additive_and_keep_existing_tokens():
    tokens = turkish_tokenize("Madde 10/A")
    assert "madde" in tokens and "10" in tokens


def test_madde_reference_does_not_match_inside_longer_number_or_word():
    assert not any(t.startswith("madde_") for t in turkish_tokenize("maddeler 12 kalem"))
