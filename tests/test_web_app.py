import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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

    with patch.object(web_app, "hybrid_search", return_value=[fake_chunk]), patch.object(
        web_app, "generate_answer", return_value="Test cevabı [1]."
    ), patch.object(web_app, "expand_query", return_value=["test sorusu"]):
        result = web_app.ask(web_app.AskRequest(question="test sorusu"))

    assert result.answer == "Test cevabı [1]."
    assert len(result.sources) == 1
    assert result.sources[0].madde_no == "1"
    assert result.confidence_level in ("high", "low")


def test_health_endpoint_reports_loading_when_not_ready():
    web_app._state.clear()
    health = web_app.health()
    assert health["status"] == "loading"


def test_health_endpoint_reports_ok_when_ready():
    web_app._state["vector_store"] = FakeVectorStore()
    health = web_app.health()
    assert health["status"] == "ok"

