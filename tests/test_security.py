import importlib.util
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.common.rate_limiter import SlidingWindowRateLimiter

_spec = importlib.util.spec_from_file_location(
    "web_app_sec", Path(__file__).resolve().parent.parent / "web" / "app.py"
)
web_app = importlib.util.module_from_spec(_spec)
sys.modules["web_app_sec"] = web_app
_spec.loader.exec_module(web_app)


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_rate_limiter_blocks_after_limit_and_reports_retry_after():
    clock = FakeClock()
    rl = SlidingWindowRateLimiter(limit=2, window_seconds=60, clock=clock)
    assert rl.check("ip") is None
    assert rl.check("ip") is None
    clock.t = 10
    retry = rl.check("ip")
    assert retry is not None and 49 <= retry <= 50


def test_rate_limiter_allows_again_after_window_and_isolates_keys():
    clock = FakeClock()
    rl = SlidingWindowRateLimiter(limit=1, window_seconds=60, clock=clock)
    assert rl.check("a") is None
    assert rl.check("b") is None  # baska istemci etkilenmez
    assert rl.check("a") is not None
    clock.t = 61
    assert rl.check("a") is None


def test_rate_limiter_blocked_request_is_not_counted():
    clock = FakeClock()
    rl = SlidingWindowRateLimiter(limit=1, window_seconds=60, clock=clock)
    rl.check("a")
    for _ in range(5):
        rl.check("a")  # reddedilenler sayilmamali
    clock.t = 61
    assert rl.check("a") is None


def test_ask_request_rejects_overlong_question():
    web_app.AskRequest(question="a" * web_app.MAX_QUESTION_LENGTH)
    with pytest.raises(ValidationError):
        web_app.AskRequest(question="a" * (web_app.MAX_QUESTION_LENGTH + 1))


def test_feedback_request_rejects_oversized_fields():
    with pytest.raises(ValidationError):
        web_app.FeedbackRequest(question="q", answer="a" * 30001, vote="up")
    with pytest.raises(ValidationError):
        web_app.FeedbackRequest(question="q", answer="a", vote="up", source_count=-1)


class _Req:
    class client:
        host = "1.2.3.4"


def test_rate_limit_dependency_raises_429_with_retry_after(monkeypatch):
    from fastapi import HTTPException

    monkeypatch.setattr(web_app, "_ask_limiter", SlidingWindowRateLimiter(limit=1, window_seconds=60))
    web_app.rate_limit_ask(_Req())
    with pytest.raises(HTTPException) as exc:
        web_app.rate_limit_ask(_Req())
    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers


def test_ask_returns_503_when_all_slots_busy(monkeypatch):
    import threading

    from fastapi import HTTPException

    sem = threading.BoundedSemaphore(1)
    sem.acquire()  # tek slot dolu
    monkeypatch.setattr(web_app, "_ask_slots", sem)
    with pytest.raises(HTTPException) as exc:
        web_app.ask(web_app.AskRequest(question="soru"))
    assert exc.value.status_code == 503


def test_ask_releases_slot_even_when_processing_fails(monkeypatch):
    import threading

    sem = threading.BoundedSemaphore(1)
    monkeypatch.setattr(web_app, "_ask_slots", sem)
    monkeypatch.setattr(web_app, "_ask", lambda req: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(RuntimeError):
        web_app.ask(web_app.AskRequest(question="soru"))
    assert sem.acquire(blocking=False)  # slot geri verilmis olmali


def test_cors_is_not_wildcard():
    assert "*" not in web_app.ALLOWED_ORIGINS
    cors = next(m for m in web_app.app.user_middleware if m.cls.__name__ == "CORSMiddleware")
    assert cors.kwargs["allow_methods"] == ["GET", "POST"]
    assert "*" not in cors.kwargs["allow_headers"]
