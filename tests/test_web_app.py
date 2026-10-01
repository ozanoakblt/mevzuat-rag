import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.generation.applicability_checker import ApplicabilityResult
from src.generation.claim_verifier import ClaimCheck, ClaimVerificationResult
from src.retrieval.pipeline import RetrievalResult

NO_CLAIM_ISSUES = ClaimVerificationResult(claims=[], checked=True)

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
    web_app._state["reranker"] = object()

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

    fake_retrieval = RetrievalResult(
        chunks=[fake_chunk], query_type=None, sub_queries=["test sorusu"]
    )
    fake_applicability = ApplicabilityResult(applicable=True, reason="", checked=True)
    with patch.object(web_app, "retrieve", return_value=fake_retrieval), patch.object(
        web_app, "generate_answer", return_value="Test cevabı [1]."
    ), patch.object(
        web_app, "check_applicability", return_value=fake_applicability
    ), patch.object(
        web_app, "verify_claims", return_value=NO_CLAIM_ISSUES
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
    web_app._state["reranker"] = object()

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

    fake_retrieval = RetrievalResult(
        chunks=[fake_chunk], query_type=None, sub_queries=["test sorusu"]
    )
    mismatched = ApplicabilityResult(
        applicable=False,
        reason="Soru kullanici kaynakli olmayan bir ariza tarif ediyor ama cevap kullanici kaynakli bozulma hukmunu uyguluyor.",
        checked=True,
    )
    with patch.object(web_app, "retrieve", return_value=fake_retrieval), patch.object(
        web_app,
        "generate_answer",
        return_value='90 gun icinde giderilir [1].\nKaynak Alıntıları:\n[1]: "Kullanici kaynakli bozulma 90 gun icinde giderilir."',
    ), patch.object(
        web_app, "check_applicability", return_value=mismatched
    ), patch.object(
        web_app, "verify_claims", return_value=NO_CLAIM_ISSUES
    ):
        result = web_app.ask(
            web_app.AskRequest(question="Kullanici kaynakli OLMAYAN bir ariza durumunda ne yapilir?")
        )

    assert result.confidence_level == "low"
    assert "UYGULANABİLİRLİK" in result.warnings


def test_ask_notes_when_applicability_check_could_not_run():
    # Eskiden check_applicability basarisiz olunca applicable=True (fail-
    # open) donuyor ve API bunu "kontrol edildi, sorun yok" ile ayni
    # gosteriyordu. Artik checked=False acikca API yanitina tasinmali ve
    # kullaniciya kontrolun calismadigi bildirilmeli - ama TEK BASINA
    # confidence_level'i "low"a CEKMEMELI (bir kota/network hatasi her
    # cevabi alarma cevirmemeli).
    web_app._state["vector_store"] = FakeVectorStore()
    web_app._state["embedder"] = object()
    web_app._state["bm25_index"] = object()
    web_app._state["reranker"] = object()

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

    fake_retrieval = RetrievalResult(
        chunks=[fake_chunk], query_type=None, sub_queries=["test sorusu"]
    )
    unchecked = ApplicabilityResult(applicable=None, reason="", checked=False)
    with patch.object(web_app, "retrieve", return_value=fake_retrieval), patch.object(
        web_app, "generate_answer", return_value="Test cevabı [1]."
    ), patch.object(
        web_app, "check_applicability", return_value=unchecked
    ), patch.object(
        web_app, "verify_claims", return_value=NO_CLAIM_ISSUES
    ):
        result = web_app.ask(web_app.AskRequest(question="test sorusu"))

    assert result.applicability_checked is False
    assert "UYGULANABİLİRLİK KONTROLÜ ÇALIŞTIRILAMADI" in result.warnings


def test_ask_flags_low_confidence_when_claim_is_unsupported():
    # Gercek vakadan (ChatGPT review): citation_guard alintiyi birebir
    # dogru bulsa ve applicability hukmun olaya uydugunu onaylasa bile,
    # iddia kaynaktan daha GUCLU/FARKLI bir sey soyluyorsa (orn.
    # "degerlendirilir" -> "kabul edilir" carpitmasi) bu ayrica
    # yakalanip dusuk guven tetiklemeli.
    web_app._state["vector_store"] = FakeVectorStore()
    web_app._state["embedder"] = object()
    web_app._state["bm25_index"] = object()
    web_app._state["reranker"] = object()

    fake_chunk = {
        "chunk_id": "doc1::m1",
        "doc_id": "kanun-6446",
        "madde_kind": "MADDE",
        "madde_no": "1",
        "fikra_no": "1",
        "bent_no": None,
        "madde_baslik": "Amaç",
        "text": "Başvuru 7 iş günü içinde değerlendirilir.",
        "rerank_score": 3.5,
        "rrf_score": 0.05,
    }
    fake_retrieval = RetrievalResult(
        chunks=[fake_chunk], query_type=None, sub_queries=["test sorusu"]
    )
    fake_applicability = ApplicabilityResult(applicable=True, reason="", checked=True)
    overstated = ClaimVerificationResult(
        claims=[
            ClaimCheck(
                text="Başvurunun kesin olarak kabul edilmesi 7 iş günü içinde tamamlanır.",
                citation_refs=[1],
                supported=False,
                reason="Kaynak 'değerlendirilir' diyor, 'kabul edilir' demiyor.",
            )
        ],
        checked=True,
    )
    with patch.object(web_app, "retrieve", return_value=fake_retrieval), patch.object(
        web_app,
        "generate_answer",
        return_value="Başvurunun kesin olarak kabul edilmesi 7 iş günü içinde tamamlanır [1].",
    ), patch.object(
        web_app, "check_applicability", return_value=fake_applicability
    ), patch.object(
        web_app, "verify_claims", return_value=overstated
    ):
        result = web_app.ask(web_app.AskRequest(question="test sorusu"))

    assert result.confidence_level == "low"
    assert "DESTEKLENMEYEN İDDİA" in result.warnings


def test_ask_passes_doc_types_through_to_retrieve():
    # Doc-type boost mantiginin kendisi artik src/retrieval/pipeline.py'de
    # yasiyor ve orada dogrudan test ediliyor (bkz.
    # tests/test_retrieval_pipeline.py::test_retrieve_applies_doc_type_boost_in_expansion_branch).
    # Burada SADECE web/app.py'nin kendi DOC_TYPES haritasini retrieve()'e
    # gercekten ilettigini dogruluyoruz.
    web_app._state["vector_store"] = FakeVectorStore()
    web_app._state["embedder"] = object()
    web_app._state["bm25_index"] = object()
    web_app._state["reranker"] = object()

    fake_chunk = {
        "chunk_id": "karar1::m1",
        "doc_id": "kurul-karari-serbest-tuketici-limiti-2026",
        "madde_kind": "MADDE",
        "madde_no": "1",
        "fikra_no": None,
        "bent_no": None,
        "madde_baslik": None,
        "text": "2026 yılı için serbest tüketici limiti 500 kWh olarak uygulanır.",
        "rerank_score": 1.0,
    }
    fake_retrieval = RetrievalResult(
        chunks=[fake_chunk], query_type="guncel_deger", sub_queries=["q"]
    )
    fake_applicability = ApplicabilityResult(applicable=True, reason="", checked=True)
    with patch.object(web_app, "retrieve", return_value=fake_retrieval) as mock_retrieve, patch.object(
        web_app, "generate_answer", return_value="Test cevabı [1]."
    ), patch.object(
        web_app, "check_applicability", return_value=fake_applicability
    ), patch.object(
        web_app, "verify_claims", return_value=NO_CLAIM_ISSUES
    ):
        web_app.ask(web_app.AskRequest(question="2026 serbest tüketici limiti kaç kWh?"))

    assert mock_retrieve.call_args.kwargs["doc_types"] is web_app.DOC_TYPES


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

