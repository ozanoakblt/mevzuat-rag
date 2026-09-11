"""
Query expansion: kullanicinin sorusunu, retrieval'in kacirabilecegi
ilgili alt-konulari da kapsayacak sekilde 2-3 alt-soruya boler.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.common.llm_router import LLMError, chat_completion_json

_CACHE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "query_expansion_cache.json"

_SIMILARITY_THRESHOLD = 0.93

_embedder_singleton = None


def _get_default_embedder():
    global _embedder_singleton
    if _embedder_singleton is None:
        from src.embedding.embedder import Embedder

        _embedder_singleton = Embedder()
    return _embedder_singleton


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


EXPANSION_SYSTEM_PROMPT = """Sen bir elektrik dagitim mevzuati arama asistanisin.
Kullanicinin sorusunu tam olarak SU YAPIYA gore 3 alt-soruya bol:

1. Orijinal soruyu degistirmeden aynen birinci alt-soru olarak kullan.
2. Ikinci alt-soru: bu islemin ADIM ADIM SURECINI sor - kim, nasil basvurur,
   hangi on kosullar var, surec nasil isler (orn. "X icin basvuru sureci nasil
   isler, hangi asamalardan gecer").
3. Ucuncu alt-soru: sureler, istisnalar veya ozel durumlari sor (orn.
   "X icin gecerli sureler ve istisnalar nelerdir").

Sadece su JSON formatinda cevap ver, baska hicbir sey yazma:
{"queries": ["soru 1", "soru 2", "soru 3"]}"""


def _cache_key(question: str) -> str:
    return hashlib.sha256(question.strip().encode("utf-8")).hexdigest()


def _load_cache() -> dict:
    if _CACHE_PATH.exists():
        try:
            return json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _entry_queries(entry) -> list[str]:
    if isinstance(entry, list):
        return entry
    return entry.get("queries", [])


def expand_query(question: str, max_queries: int = 3, embedder=None) -> list[str]:
    """
    question icin 1-max_queries arasi alt-soru doner.

    Iki katmanli cache: (1) tam eslesme - hizli yol; (2) anlamsal eslesme
    - embedding benzerligi >= esik ise LLM'e gitmeden onceki alt-sorular
    kullanilir. Bu, kullanicinin ayni soruyu farkli ifade etmesi
    durumunda da tutarli sonuc saglar. Embedding hesaplamasi tamamen
    yerel/ucretsizdir.
    """
    cache = _load_cache()
    key = _cache_key(question)

    if key in cache:
        return _entry_queries(cache[key])[:max_queries]

    query_embedding: list[float] | None = None
    try:
        active_embedder = embedder or _get_default_embedder()
        query_embedding = active_embedder.embed_query(question)
    except Exception:
        query_embedding = None

    if query_embedding is not None:
        best_entry = None
        best_similarity = 0.0
        for entry in cache.values():
            if not isinstance(entry, dict) or "embedding" not in entry:
                continue
            similarity = _cosine_similarity(query_embedding, entry["embedding"])
            if similarity > best_similarity:
                best_similarity = similarity
                best_entry = entry
        if best_entry is not None and best_similarity >= _SIMILARITY_THRESHOLD:
            return _entry_queries(best_entry)[:max_queries]

    try:
        result = chat_completion_json(EXPANSION_SYSTEM_PROMPT, question, temperature=0.0)
        queries = result.get("queries", [])
        queries = [q.strip() for q in queries if isinstance(q, str) and q.strip()]
        if not queries:
            return [question]
        cache[key] = {
            "question": question,
            "embedding": query_embedding,
            "queries": queries,
        }
        _save_cache(cache)
        return queries[:max_queries]
    except LLMError:
        return [question]
