from pathlib import Path
p = Path("src/retrieval/query_expansion.py")
s = p.read_text(encoding="utf-8")

old_import = """from src.common.llm_router import LLMError, chat_completion_json"""
new_import = """import hashlib
import json
from pathlib import Path

from src.common.llm_router import LLMError, chat_completion_json

_CACHE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "query_expansion_cache.json\""""
assert old_import in s, "import satiri bulunamadi"
s = s.replace(old_import, new_import)

old_fn = """def expand_query(question: str, max_queries: int = 3) -> list[str]:
    \"\"\"
    question icin 1-max_queries arasi alt-soru doner. Groq API hatasi
    olursa (rate limit, key yok vb.) orijinal soruyu tek elemanli liste
    olarak doner - expansion basarisiz olursa sistem cokmemeli, sadece
    eski (expansion'siz) davranisa geri dusmeli.
    \"\"\"
    try:
        result = chat_completion_json(EXPANSION_SYSTEM_PROMPT, question, temperature=0.0)
        queries = result.get("queries", [])
        queries = [q.strip() for q in queries if isinstance(q, str) and q.strip()]
        if not queries:
            return [question]
        return queries[:max_queries]
    except LLMError:
        return [question]"""
new_fn = """def _cache_key(question: str) -> str:
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


def expand_query(question: str, max_queries: int = 3) -> list[str]:
    \"\"\"
    question icin 1-max_queries arasi alt-soru doner.

    Disk-tabanli cache: ayni soru tekrar geldiginde LLM'e hic gitmeden
    onceki alt-sorulari doner - hem run'lar arasi tutarsizligi giderir
    hem kota korur. Sadece BASARILI bir expansion cache'lenir; hata
    sonucu donen [question] fallback'i asla cache'lenmez.
    \"\"\"
    cache = _load_cache()
    key = _cache_key(question)
    if key in cache:
        return cache[key][:max_queries]

    try:
        result = chat_completion_json(EXPANSION_SYSTEM_PROMPT, question, temperature=0.0)
        queries = result.get("queries", [])
        queries = [q.strip() for q in queries if isinstance(q, str) and q.strip()]
        if not queries:
            return [question]
        cache[key] = queries
        _save_cache(cache)
        return queries[:max_queries]
    except LLMError:
        return [question]"""
assert old_fn in s, "expand_query fonksiyonu bulunamadi"
s = s.replace(old_fn, new_fn)

p.write_text(s, encoding="utf-8")
print("Tamamlandi: query expansion cache eklendi.")
