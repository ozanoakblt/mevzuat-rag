"""
Faz 12: Basit FastAPI backend.

Mevcut pipeline'ı (Faz 4-9: embedding, hybrid retrieval, reranker,
generation, citation guard) hiçbir mantığı tekrar yazmadan, doğrudan
import edip bir HTTP API olarak sunar.

Çalıştırma:
    uvicorn web.app:app --reload
    (sonra tarayıcıda http://127.0.0.1:8000 açın)

Bileşenler (embedder, vector store, bm25 index, reranker) sunucu
başlarken BİR KEZ yüklenir (her istekte değil) — ilk istek değil, ilk
sunucu açılışı birkaç saniye sürer.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.common.rate_limiter import SlidingWindowRateLimiter
from src.embedding.embedder import Embedder
from src.embedding.vector_store import VectorStore, load_all_chunks
from src.generation.answer_generator import generate_answer
from src.generation.applicability_checker import check_applicability
from src.generation.citation_guard import format_guard_warnings, run_guard
from src.generation.claim_verifier import verify_claims
from src.ingestion.sources import SOURCES
from src.retrieval.bm25_index import BM25Index
from src.retrieval.pipeline import retrieve
from src.retrieval.question_bank import QuestionBank
from src.retrieval.reranker import Reranker

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
VECTOR_STORE_DIR = ROOT / "data" / "vector_store"
STATIC_DIR = Path(__file__).resolve().parent / "static"
# Kullanicinin 👍/👎 geri bildirimini kalici olarak biriktirir - onceden
# arayuzdeki oy butonlari sadece gorsel bir CSS class toggle'iydi, hicbir
# yere kaydedilmiyordu (gercek kullanim verisi tamamen kayboluyordu).
# JSONL: her satir bagimsiz bir kayit, append-only, kolayca analiz edilir.
FEEDBACK_LOG_PATH = ROOT / "data" / "user_feedback.jsonl"


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


# --- Guvenlik/kaynak sinirlari (hepsi env ile ayarlanabilir) ---
# Her /api/ask cagrisi 3 LLM istegi tetikler (cevap + applicability + claim
# verifier) - kontrolsuz istek API kotasini ve maliyeti hizla tuketir.
MAX_QUESTION_LENGTH = 2000
ASK_RATE_LIMIT_PER_MINUTE = _env_int("ASK_RATE_LIMIT_PER_MINUTE", 10)
FEEDBACK_RATE_LIMIT_PER_MINUTE = _env_int("FEEDBACK_RATE_LIMIT_PER_MINUTE", 30)
MAX_CONCURRENT_ASKS = _env_int("MAX_CONCURRENT_ASKS", 3)
# Frontend ayni origin'den servis edildigi icin CORS normalde gerekmez; baska
# bir origin'den erisim gerekirse ALLOWED_ORIGINS="https://a.com,https://b.com".
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000"
    ).split(",")
    if o.strip()
]

_ask_limiter = SlidingWindowRateLimiter(ASK_RATE_LIMIT_PER_MINUTE)
_feedback_limiter = SlidingWindowRateLimiter(FEEDBACK_RATE_LIMIT_PER_MINUTE)
_ask_slots = threading.BoundedSemaphore(MAX_CONCURRENT_ASKS)


def _client_key(request: Request) -> str:
    # Ters-proxy arkasinda X-Forwarded-For'a KASITLI olarak guvenilmiyor
    # (istemci sahteleyip limiti asabilir); proxy kullaniliyorsa limit
    # proxy seviyesinde uygulanmali.
    return request.client.host if request.client else "unknown"


def _rate_limit(limiter: SlidingWindowRateLimiter, request: Request) -> None:
    retry_after = limiter.check(_client_key(request))
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="Çok fazla istek. Lütfen biraz bekleyip tekrar deneyin.",
            headers={"Retry-After": str(int(retry_after) + 1)},
        )


def rate_limit_ask(request: Request) -> None:
    _rate_limit(_ask_limiter, request)


def rate_limit_feedback(request: Request) -> None:
    _rate_limit(_feedback_limiter, request)

DOC_TITLES = {s.doc_id: s.title for s in SOURCES}
# doc_type boost ve diger retrieval sabitleri artik src/retrieval/pipeline.py'de
# tek bir yerde tutuluyor (bkz. o modulun docstring'i - eskiden web/app.py
# ve scripts/run_eval.py arasinda surukleme/drift riski vardi).
DOC_TYPES = {s.doc_id: s.doc_type for s in SOURCES}
# Temporal/version-aware retrieval (bkz. src/retrieval/temporal.py):
# version_group'u olan SourceDoc'lar icin {doc_id: (version_group, effective_from)}.
DOC_VERSIONS = {
    s.doc_id: (s.version_group, date.fromisoformat(s.effective_from))
    for s in SOURCES
    if s.version_group and s.effective_from
}

# --- Bileşenler: sunucu başlarken bir kez yüklenir ---
_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Pipeline bileşenleri yükleniyor...")
    t0 = time.time()
    chunks = load_all_chunks(PROCESSED_DIR)
    _state["embedder"] = Embedder()
    _state["vector_store"] = VectorStore(persist_dir=VECTOR_STORE_DIR)
    _state["bm25_index"] = BM25Index(chunks)
    _state["reranker"] = Reranker()
    _state["question_bank"] = QuestionBank.build(
        _state["embedder"], ROOT / "eval" / "eval_set.json"
    )
    print(f"Pipeline hazır ({time.time() - t0:.1f}s, {len(chunks)} chunk).")
    yield
    _state.clear()


app = FastAPI(title="Elektrik Dağıtım Mevzuat Asistanı", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class AskRequest(BaseModel):
    question: str = Field(max_length=MAX_QUESTION_LENGTH)


class SourceOut(BaseModel):
    doc_title: str
    madde_kind: str
    madde_no: str
    fikra_no: str | None
    bent_no: str | None
    madde_baslik: str | None
    text: str
    rerank_score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceOut]
    confidence_level: str  # "high" | "low"
    warnings: str
    applicability_checked: bool
    claim_verification_checked: bool
    suggested_questions: list[str] = []


class FeedbackRequest(BaseModel):
    # Uzunluk sinirlari, feedback log dosyasinin kotuye kullanimla
    # sisirilmesini onler.
    question: str = Field(max_length=MAX_QUESTION_LENGTH)
    answer: str = Field(max_length=30000)
    vote: str = Field(max_length=10)  # "up" | "down"
    confidence_level: str | None = Field(default=None, max_length=20)
    source_count: int = Field(default=0, ge=0, le=1000)


@app.post("/api/ask", response_model=AskResponse, dependencies=[Depends(rate_limit_ask)])
def ask(req: AskRequest) -> AskResponse:
    # Ayni anda islenen cevap sayisini sinirla (embedding/reranker CPU'da
    # calisiyor, her cevap 3 LLM cagrisi) - dolu ise bekletmek yerine 503.
    if not _ask_slots.acquire(blocking=False):
        raise HTTPException(
            status_code=503,
            detail="Sistem şu an meşgul. Lütfen birkaç saniye sonra tekrar deneyin.",
            headers={"Retry-After": "5"},
        )
    try:
        return _ask(req)
    finally:
        _ask_slots.release()


def _ask(req: AskRequest) -> AskResponse:
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Soru boş olamaz.")

    vector_store: VectorStore = _state["vector_store"]
    if vector_store.count() == 0:
        raise HTTPException(
            status_code=503,
            detail="Vektör index boş. Önce scripts/build_index.py çalıştırın.",
        )

    retrieval = retrieve(
        question,
        _state["embedder"],
        vector_store,
        _state["bm25_index"],
        _state["reranker"],
        doc_types=DOC_TYPES,
        doc_versions=DOC_VERSIONS,
    )
    top_chunks = retrieval.chunks

    try:
        answer = generate_answer(question, top_chunks, doc_titles=DOC_TITLES)
    except Exception as exc:
        import traceback
        error_detail = traceback.format_exc()
        with open("last_error.log", "w", encoding="utf-8") as f:
            f.write(error_detail)
        print("=" * 60)
        print("GENERATE_ANSWER HATASI:")
        print(error_detail)
        print("=" * 60)
        raise
    guard = run_guard(answer, top_chunks)
    applicability = check_applicability(question, answer, retrieved_chunks=top_chunks)
    claim_verification = verify_claims(answer, top_chunks)

    sources = [
        SourceOut(
            doc_title=DOC_TITLES.get(c["doc_id"], c["doc_id"]),
            madde_kind=c["madde_kind"],
            madde_no=c["madde_no"],
            fikra_no=c.get("fikra_no"),
            bent_no=c.get("bent_no"),
            madde_baslik=c.get("madde_baslik"),
            text=c["text"],
            rerank_score=c["rerank_score"],
        )
        for c in top_chunks
    ]

    warnings = format_guard_warnings(guard)
    is_low_confidence = guard.is_low_confidence
    if applicability.checked and applicability.applicable is False:
        is_low_confidence = True
        reason_suffix = f" ({applicability.reason})" if applicability.reason else ""
        warnings = (
            warnings + "\n" if warnings else ""
        ) + f"UYARI - UYGULANABİLİRLİK: Bulunan hükümler, sorudaki spesifik durumla tam örtüşmüyor olabilir{reason_suffix}. Kaynakları dikkatle kontrol edin."
    elif not applicability.checked:
        # Eskiden kontrol basarisiz olunca applicable=True (fail-open)
        # donup sessizce "kontrol edildi, sorun yok" ile ayni gorunuyordu.
        # Artik bu durum ayrica isaretleniyor - confidence'i zorla "low"a
        # CEKMIYORUZ (tek basina bir network/kota hatasi her cevabi
        # alarma cevirmemeli), ama API tuketicisi applicability_checked
        # alanindan bu kontrolun hic calismadigini gorebilir.
        warnings = (
            warnings + "\n" if warnings else ""
        ) + "NOT - UYGULANABİLİRLİK KONTROLÜ ÇALIŞTIRILAMADI: Bu cevap için ayrı uygulanabilirlik denetimi yapılamadı, sonuç bu açıdan doğrulanmamıştır."

    if claim_verification.has_unsupported_claims:
        is_low_confidence = True
        unsupported_texts = "; ".join(c.text for c in claim_verification.unsupported_claims)
        warnings = (
            warnings + "\n" if warnings else ""
        ) + f"UYARI - DESTEKLENMEYEN İDDİA: Şu iddia(lar) gösterdiği kaynaktan daha güçlü/farklı bir şey söylüyor olabilir: {unsupported_texts}. Kaynak metni dikkatle karşılaştırın."

    suggested_questions: list[str] = []
    bank = _state.get("question_bank")
    if is_low_confidence and bank is not None:
        # Dusuk guvenli cevapta "bunu mu sormak istediniz?" onerileri
        # (soru bankasindan en yakin sorular, ekstra LLM cagrisi yok).
        suggested_questions = bank.suggest(_state["embedder"].embed_query(question))

    return AskResponse(
        answer=answer,
        sources=sources,
        confidence_level="low" if is_low_confidence else "high",
        warnings=warnings,
        applicability_checked=applicability.checked,
        claim_verification_checked=claim_verification.checked,
        suggested_questions=suggested_questions,
    )


@app.post("/api/feedback", dependencies=[Depends(rate_limit_feedback)])
def feedback(req: FeedbackRequest) -> dict:
    if req.vote not in ("up", "down"):
        raise HTTPException(status_code=400, detail="vote 'up' veya 'down' olmalı.")
    FEEDBACK_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": req.question,
        "answer": req.answer,
        "vote": req.vote,
        "confidence_level": req.confidence_level,
        "source_count": req.source_count,
    }
    with open(FEEDBACK_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"status": "ok"}


@app.get("/api/health")
def health() -> dict:
    ready = "vector_store" in _state and _state["vector_store"].count() > 0
    return {"status": "ok" if ready else "loading"}


# Statik dosyalar (CSS/JS) ve ana sayfa
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))




