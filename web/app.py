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

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.embedding.embedder import Embedder
from src.embedding.vector_store import VectorStore, load_all_chunks
from src.generation.answer_generator import generate_answer
from src.generation.citation_guard import format_guard_warnings, run_guard
from src.ingestion.sources import SOURCES
from src.retrieval.bm25_index import BM25Index
from src.retrieval.hybrid import hybrid_search
from src.retrieval.query_expansion import expand_query
from src.retrieval.reranker import Reranker

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
VECTOR_STORE_DIR = ROOT / "data" / "vector_store"
STATIC_DIR = Path(__file__).resolve().parent / "static"

CANDIDATE_POOL_SIZE = 30
FINAL_TOP_K = 8
DOC_TITLES = {s.doc_id: s.title for s in SOURCES}

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
    print(f"Pipeline hazır ({time.time() - t0:.1f}s, {len(chunks)} chunk).")
    yield
    _state.clear()


app = FastAPI(title="Elektrik Dağıtım Mevzuat Asistanı", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str


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


@app.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Soru boş olamaz.")

    vector_store: VectorStore = _state["vector_store"]
    if vector_store.count() == 0:
        raise HTTPException(
            status_code=503,
            detail="Vektör index boş. Önce scripts/build_index.py çalıştırın.",
        )

    sub_queries = expand_query(question)
    candidates_by_id: dict[str, dict] = {}
    guard_ids: list[str] = []
    for sq in sub_queries:
        sq_results = hybrid_search(
            sq,
            _state["embedder"],
            vector_store,
            _state["bm25_index"],
            top_k=CANDIDATE_POOL_SIZE,
        )
        for i, r in enumerate(sq_results):
            cid = r["chunk_id"]
            if cid not in candidates_by_id or r["rrf_score"] > candidates_by_id[cid]["rrf_score"]:
                candidates_by_id[cid] = r
            if i < 5 and cid not in guard_ids:
                guard_ids.append(cid)
    candidates = sorted(candidates_by_id.values(), key=lambda c: c["rrf_score"], reverse=True)
    guard_pool = [candidates_by_id[cid] for cid in guard_ids]
    top_chunks = _state["reranker"].rerank_with_safety_net(
        question, candidates, top_k=FINAL_TOP_K, guard_pool=guard_pool
    )

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

    return AskResponse(
        answer=answer,
        sources=sources,
        confidence_level="low" if guard.is_low_confidence else "high",
        warnings=format_guard_warnings(guard),
    )


@app.get("/api/health")
def health() -> dict:
    ready = "vector_store" in _state and _state["vector_store"].count() > 0
    return {"status": "ok" if ready else "loading"}


# Statik dosyalar (CSS/JS) ve ana sayfa
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))




