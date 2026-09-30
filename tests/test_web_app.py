import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.generation.applicability_checker import ApplicabilityResult

_spec = importlib.util.spec_from_file_location(
    "web_app", Path(__file__).resolve().parent.parent / "web" / "app.py"
)
web_app = importlib.util.module_from_spec(_spec)
sys.modules["web_app"] = web_app  # pydantic'in forward-ref çözümlemesi için gerekli
_spec.loader.exec_module(web_app)


class FakeVectorStore:
    def count(self):
        return 42


def test_ask_empty_question_raises_400():
    from fastapi import HTTPException

    web_app._state["vector_store"] = FakeVectorStore()
    try:
        web_app.ask(web_app.AskRequest(question="   "))
        assert False, "HTTPException bekleniyordu"
    except HTTPException as exc:
        assert exc.status_code == 400


def test_ask_empty_vector_store_raises_503():
    from fastapi import HTTPException

    class EmptyStore:
        def count(self):
            return 0

    web_app._state["vector_store"] = EmptyStore()
    try:
        web_app.ask(web_app.AskRequest(question="test soru"))
        assert False, "HTTPException bekleniyordu"
    except HTTPException as exc:
        assert exc.status_code == 503


def test_ask_happy_path_returns_structured_response():
    web_app._state["vector_store"] = FakeVectorStore()
    web_app._state["embedder"] = object()
    web_app._state["bm25_index"] = object()

    fake_chunk = {
        "chunk_id": "doc1::m1",
        "doc_id": "kanun-6446",
        "madde_kind": "MADDE",
        "madde_no": "1",
        "fikra_no": "1",
        "bent_no": None,
        "madde_baslik": "Amaç",
        "text": "Bu maddenin amacı test etmektir.",
        "rerank_score": 3.5,
        "rrf_score": 0.05,
    }

    class FakeReranker:
        def rerank_with_safety_net(self, query, candidates, top_k=5, guard_pool=None):
            return [fake_chunk]

    web_app._state["reranker"] = FakeReranker()

    fake_applicability = ApplicabilityResult(applicable=True, reason="", checked=True)
    with patch.object(web_app, "hybrid_search", return_value=[fake_chunk]), patch.object(
        web_app, "generate_answer", return_value="Test cevabı [1]."
    ), patch.object(web_app, "expand_query", return_value=["test sorusu"]), patch.object(
        web_app, "get_query_type", return_value="genel_hukum"
    ), patch.object(
        web_app, "check_applicability", return_value=fake_applicability
    ):
        result = web_app.ask(web_app.AskRequest(question="test sorusu"))

    assert result.answer == "Test cevabı [1]."
    assert len(result.sources) == 1
    assert result.sources[0].madde_no == "1"
    assert result.confidence_level in ("high", "low")


def test_ask_flags_low_confidence_when_applicability_check_fails():
    # Gercek bir vakadan (EPDK sinav testi, Soru 40): citation_guard
    # alintilari gorundu diye onay verse bile, cevabin MANTIGI soruya
    # uymuyorsa (yanlis hukum ailesi uygulanmis) applicability kontrolu
    # bunu ayrica yakalayip dusuk guven tetiklemeli.
    web_app._state["vector_store"] = FakeVectorStore()
    web_app._state["embedder"] = object()
    web_app._state["bm25_index"] = object()

    fake_chunk = {
        "chunk_id": "doc1::m1",
        "doc_id": "kanun-6446",
        "madde_kind": "MADDE",
        "madde_no": "1",
        "fikra_no": "1",
        "bent_no": None,
        "madde_baslik": "Amaç",
        "text": "Kullanici kaynakli bozulma 90 gun icinde giderilir.",
        "rerank_score": 3.5,
        "rrf_score": 0.05,
    }

    class FakeReranker:
        def rerank_with_safety_net(self, query, candidates, top_k=5, guard_pool=None):
            return [fake_chunk]

    web_app._state["reranker"] = FakeReranker()

    mismatched = ApplicabilityResult(
        applicable=False,
        reason="Soru kullanici kaynakli olmayan bir ariza tarif ediyor ama cevap kullanici kaynakli bozulma hukmunu uyguluyor.",
        checked=True,
    )
    with patch.object(web_app, "hybrid_search", return_value=[fake_chunk]), patch.object(
        web_app,
        "generate_answer",
        return_value='90 gun icinde giderilir [1].\nKaynak Alıntıları:\n[1]: "Kullanici kaynakli bozulma 90 gun icinde giderilir."',
    ), patch.object(web_app, "expand_query", return_value=["test sorusu"]), patch.object(
        web_app, "get_query_type", return_value="genel_hukum"
    ), patch.object(
        web_app, "check_applicability", return_value=mismatched
    ):
        result = web_app.ask(
            web_app.AskRequest(question="Kullanici kaynakli OLMAYAN bir ariza durumunda ne yapilir?")
        )

    assert result.confidence_level == "low"
    assert "UYGULANABİLİRLİK" in result.warnings


def test_ask_boosts_preferred_doc_type_for_guncel_deger_queries():
    # Gercek bir vakadan (EPDK sinav testi, Soru 5): "2026 limiti nedir"
    # gibi sorular sadece yillik Kurul Kararlarinda bulunuyor, Yonetmelik/
    # Kanun'da degil - query_type="guncel_deger" oldugunda "karar" turu
    # kaynaklarin rrf_score'u artmali.
    web_app._state["vector_store"] = FakeVectorStore()
    web_app._state["embedder"] = object()
    web_app._state["bm25_index"] = object()
    web_app._state["reranker"] = type(
        "FakeReranker", (), {"rerank_with_safety_net": lambda self, query, candidates, top_k=5, guard_pool=None: candidates}
    )()

    karar_chunk = {
        "chunk_id": "karar1::m1",
        "doc_id": "kurul-karari-serbest-tuketici-limiti-2026",
        "madde_kind": "MADDE",
        "madde_no": "1",
        "fikra_no": None,
        "bent_no": None,
        "madde_baslik": None,
        "text": "2026 yılı için serbest tüketici limiti 500 kWh olarak uygulanır.",
        "rerank_score": 1.0,
        "rrf_score": 0.02,
    }
    yonetmelik_chunk = {
        "chunk_id": "yonet1::m1",
        "doc_id": "kanun-6446",
        "madde_kind": "MADDE",
        "madde_no": "1",
        "fikra_no": None,
        "bent_no": None,
        "madde_baslik": None,
        "text": "Alakasiz bir yonetmelik metni.",
        "rerank_score": 1.0,
        "rrf_score": 0.021,  # baslangicta karar_chunk'tan hafif yuksek
    }

    web_app.DOC_TYPES["kurul-karari-serbest-tuketici-limiti-2026"] = "karar"
    web_app.DOC_TYPES["kanun-6446"] = "kanun"

    original_karar_score = karar_chunk["rrf_score"]

    def fake_hybrid_search(*args, **kwargs):
        return [karar_chunk, yonetmelik_chunk]

    fake_applicability = ApplicabilityResult(applicable=True, reason="", checked=True)
    with patch.object(web_app, "hybrid_search", side_effect=fake_hybrid_search), patch.object(
        web_app, "generate_answer", return_value="Test cevabı [1]."
    ), patch.object(web_app, "expand_query", return_value=["test sorusu"]), patch.object(
        web_app, "get_query_type", return_value="guncel_deger"
    ), patch.object(
        web_app, "check_applicability", return_value=fake_applicability
    ):
        web_app.ask(web_app.AskRequest(question="2026 serbest tüketici limiti kaç kWh?"))

    # ask() sirasinda karar_chunk'in rrf_score'u gercekten boost edilmis
    # (yerinde mutasyonla) ve artik yonetmelik_chunk'i gecmis olmali -
    # boostsuz durumda yonetmelik_chunk hafif onde basliyordu (0.021 > 0.02).
    assert karar_chunk["rrf_score"] == original_karar_score * web_app.DOC_TYPE_BOOST_MULTIPLIER
    assert karar_chunk["rrf_score"] > yonetmelik_chunk["rrf_score"]


def test_feedback_rejects_invalid_vote_value():
    from fastapi import HTTPException

    try:
        web_app.feedback(
            web_app.FeedbackRequest(question="soru", answer="cevap", vote="maybe")
        )
        assert False, "HTTPException bekleniyordu"
    except HTTPException as exc:
        assert exc.status_code == 400


def test_feedback_appends_jsonl_record(tmp_path, monkeypatch):
    import json

    log_path = tmp_path / "user_feedback.jsonl"
    monkeypatch.setattr(web_app, "FEEDBACK_LOG_PATH", log_path)

    result = web_app.feedback(
        web_app.FeedbackRequest(
            question="Kesinti tazminatı nasıl hesaplanır?",
            answer="Test cevabı [1].",
            vote="down",
            confidence_level="low",
            source_count=3,
        )
    )

    assert result == {"status": "ok"}
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["question"] == "Kesinti tazminatı nasıl hesaplanır?"
    assert record["vote"] == "down"
    assert record["confidence_level"] == "low"
    assert record["source_count"] == 3
    assert "timestamp" in record


def test_feedback_appends_multiple_records_without_overwriting(tmp_path, monkeypatch):
    log_path = tmp_path / "user_feedback.jsonl"
    monkeypatch.setattr(web_app, "FEEDBACK_LOG_PATH", log_path)

    web_app.feedback(web_app.FeedbackRequest(question="s1", answer="c1", vote="up"))
    web_app.feedback(web_app.FeedbackRequest(question="s2", answer="c2", vote="down"))

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2


def test_health_endpoint_reports_loading_when_not_ready():
    web_app._state.clear()
    health = web_app.health()
    assert health["status"] == "loading"


def test_health_endpoint_reports_ok_when_ready():
    web_app._state["vector_store"] = FakeVectorStore()
    health = web_app.health()
    assert health["status"] == "ok"

