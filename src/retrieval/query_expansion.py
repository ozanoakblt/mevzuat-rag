"""
Query expansion: kullanicinin sorusunu, retrieval'in kacirabilecegi
ilgili alt-konulari da kapsayacak sekilde 2-3 alt-soruya boler.

Neden gerekli: tek bir embedding/BM25 sorgusu, sorunun sadece en belirgin
yonunu yakalar. Alt-sorulara bolup her biri icin ayri arama yapmak, ilgili
ama farkli kelime dagarcigina sahip maddelerin de aday havuzuna girmesini
saglar.
"""
from __future__ import annotations

from src.common.groq_client import GroqError, chat_completion_json

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


def expand_query(question: str, max_queries: int = 3) -> list[str]:
    """
    question icin 1-max_queries arasi alt-soru doner. Groq API hatasi
    olursa (rate limit, key yok vb.) orijinal soruyu tek elemanli liste
    olarak doner - expansion basarisiz olursa sistem cokmemeli, sadece
    eski (expansion'siz) davranisa geri dusmeli.
    """
    try:
        result = chat_completion_json(EXPANSION_SYSTEM_PROMPT, question, temperature=0.0)
        queries = result.get("queries", [])
        queries = [q.strip() for q in queries if isinstance(q, str) and q.strip()]
        if not queries:
            return [question]
        return queries[:max_queries]
    except GroqError:
        return [question]

