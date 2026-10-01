import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.retrieval.temporal import (
    DEFAULT_LATEST_BOOST,
    FUTURE_VERSION_PENALTY,
    apply_temporal_adjustment,
    extract_query_date,
)


def test_extract_query_date_explicit_ddmmyyyy():
    assert extract_query_date("27.01.2026 tarihinden itibaren gecerli mi?") == date(2026, 1, 27)


def test_extract_query_date_explicit_with_slash():
    assert extract_query_date("27/01/2026 tarihli metin") == date(2026, 1, 27)


def test_extract_query_date_month_year_turkish():
    assert extract_query_date("2026 yılı Haziranında ne degisti?") == date(2026, 6, 1)


def test_extract_query_date_month_then_year():
    assert extract_query_date("Haziran 2026 degisikligi neydi?") == date(2026, 6, 1)


def test_extract_query_date_bare_year_defaults_to_january():
    assert extract_query_date("2026 itibarıyla baglanti suresi kac gun?") == date(2026, 1, 1)


def test_extract_query_date_returns_none_when_no_date():
    assert extract_query_date("Baglanti gorusunun gecerlilik suresi nedir?") is None


def test_extract_query_date_ignores_invalid_explicit_date():
    # 31/02 gecersiz bir tarih - bu kalibi atlayip diger kaliplere (veya
    # None'a) dusmeli, exception firlatmamali.
    assert extract_query_date("31/02/2026 gibi olmayan bir tarih") in (None, date(2026, 1, 1))


DOC_VERSIONS = {
    "doc-old": ("grup-x", date(2026, 1, 27)),
    "doc-new": ("grup-x", date(2026, 6, 25)),
}


def _result(doc_id, rrf_score=0.05):
    return {"doc_id": doc_id, "chunk_id": f"{doc_id}::m1", "rrf_score": rrf_score}


def test_apply_temporal_adjustment_no_date_boosts_latest_version():
    results = [_result("doc-old"), _result("doc-new")]
    apply_temporal_adjustment(results, query_date=None, doc_versions=DOC_VERSIONS)

    old_r = next(r for r in results if r["doc_id"] == "doc-old")
    new_r = next(r for r in results if r["doc_id"] == "doc-new")
    assert new_r["rrf_score"] == 0.05 * DEFAULT_LATEST_BOOST
    assert old_r["rrf_score"] == 0.05  # degismedi
    assert new_r["rrf_score"] > old_r["rrf_score"]


def test_apply_temporal_adjustment_query_date_before_amendment_penalizes_future_version():
    # Soru acikca 27.01.2026 tarihini (eski versiyonun yururluk tarihi)
    # kastediyor - 25.06.2026'da yururluge giren degisiklik HENUZ
    # gecerli degildi, cezalandirilmali.
    results = [_result("doc-old"), _result("doc-new")]
    apply_temporal_adjustment(results, query_date=date(2026, 2, 1), doc_versions=DOC_VERSIONS)

    old_r = next(r for r in results if r["doc_id"] == "doc-old")
    new_r = next(r for r in results if r["doc_id"] == "doc-new")
    assert old_r["rrf_score"] == 0.05  # henuz yururlukteydi, dokunulmadi
    assert new_r["rrf_score"] == 0.05 * FUTURE_VERSION_PENALTY
    assert old_r["rrf_score"] > new_r["rrf_score"]


def test_apply_temporal_adjustment_query_date_after_amendment_does_not_penalize_either():
    # Sorgu tarihi degisiklikten SONRA - her iki belge de o tarihte
    # "gecerliydi" (eski metin hala tarihsel olarak var olmustu), hicbiri
    # cezalandirilmaz (sadece effective_from > query_date olan cezalanir).
    results = [_result("doc-old"), _result("doc-new")]
    apply_temporal_adjustment(results, query_date=date(2026, 7, 1), doc_versions=DOC_VERSIONS)

    assert all(r["rrf_score"] == 0.05 for r in results)


def test_apply_temporal_adjustment_single_version_present_is_noop():
    # version_group'ta sadece TEK belge sonuclarda varsa (digeri hic
    # bulunamadiysa), secim belirsizligi yok - dokunulmamali.
    results = [_result("doc-old")]
    apply_temporal_adjustment(results, query_date=None, doc_versions=DOC_VERSIONS)
    assert results[0]["rrf_score"] == 0.05


def test_apply_temporal_adjustment_ignores_docs_without_version_group():
    results = [_result("doc-unrelated")]
    apply_temporal_adjustment(results, query_date=None, doc_versions=DOC_VERSIONS)
    assert results[0]["rrf_score"] == 0.05
