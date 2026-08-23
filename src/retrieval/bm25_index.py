"""
Faz 5: BM25 (anahtar kelime / tam terim) arama.

Embedding aramasının (Faz 4) zayıf olduğu durumları kapatır: spesifik
hukuki terimler, madde numaraları, nadir geçen kelimeler. rank_bm25
kullanılıyor (saf Python, ücretsiz, ek servis gerektirmez — brief madde 2).

Persistans: BM25 index'i diske kaydetmiyoruz — 966 chunk'lık bir korpus
için yeniden oluşturmak (~1 saniyenin altında) diskte saklamaktan daha
basit ve "stale index" riski taşımıyor.
"""
from __future__ import annotations

from rank_bm25 import BM25Okapi

from .tokenizer import turkish_tokenize


class BM25Index:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self._tokenized_corpus = [
            turkish_tokenize(c.get("embedding_text") or c["text"]) for c in chunks
        ]
        self._bm25 = BM25Okapi(self._tokenized_corpus)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        query_tokens = turkish_tokenize(query)
        scores = self._bm25.get_scores(query_tokens)

        ranked_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:top_k]

        results = []
        for idx in ranked_indices:
            if scores[idx] <= 0:
                continue  # hiç eşleşmeyen sonuçları döndürme
            chunk = self.chunks[idx]
            results.append({**chunk, "bm25_score": float(scores[idx])})
        return results
