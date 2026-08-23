"""
Faz 7: Reranker.

Hybrid retrieval (Faz 6) sorgu ve pasajı AYRI AYRI embed eder (bi-encoder),
bu hızlıdır ama sınırlı bir doğruluk tavanı vardır. Reranker ise sorgu ve
pasajı BİRLİKTE tek bir modele verir (cross-encoder) — çok daha yavaştır
(bu yüzden sadece ilk N adaya uygulanır, tüm korpusa değil) ama alaka
tahmini çok daha isabetlidir. Tipik kullanım: hybrid'den top-20 al,
reranker ile top-5'e indir.

Model: cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 — çok dilli (Türkçe
dahil), küçük (~130 MB), ücretsiz. Daha büyük/isabetli alternatif
(BAAI/bge-reranker-v2-m3, ~2 GB) gerekirse EMBEDDING_MODEL deseniyle
aynı şekilde .env üzerinden değiştirilebilir.
"""
from __future__ import annotations

import os
from typing import Protocol

DEFAULT_RERANKER_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


class CrossEncoderModel(Protocol):
    def predict(self, pairs: list[tuple[str, str]]) -> list[float]: ...


class Reranker:
    def __init__(self, model: CrossEncoderModel | None = None, model_name: str | None = None):
        if model is not None:
            self._model = model
        else:
            from sentence_transformers import CrossEncoder

            name = model_name or os.environ.get("RERANKER_MODEL", DEFAULT_RERANKER_MODEL)
            self._model = CrossEncoder(name)

    def rerank(self, query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
        """
        candidates: hybrid_search() çıktısı gibi, her biri en az "text"
        alanı olan dict listesi. rerank_score eklenip yeniden sıralanır.
        """
        if not candidates:
            return []

        pairs = [(query, c["text"]) for c in candidates]
        scores = self._model.predict(pairs)

        scored = [
            {**c, "rerank_score": float(score)} for c, score in zip(candidates, scores)
        ]
        scored.sort(key=lambda c: c["rerank_score"], reverse=True)
        return scored[:top_k]

    def rerank_with_safety_net(
        self, query: str, candidates: list[dict], top_k: int = 5, guard_top_n: int = 3
    ) -> list[dict]:
        """
        rerank()'in aynısı, tek farkla: hybrid'in en güçlü ilk `guard_top_n`
        sonucundan (candidates listesinin başı — hybrid_search zaten RRF
        skoruna göre sıralı döner) final listede HİÇ olmayanlar varsa, en
        zayıf reranker sonuçlarının yerine geri eklenir (en güçlü kurtarılan
        önce, en zayıf reranker sonucunun yerine).

        Neden guard_top_n=1 değil de 3: ilk versiyon sadece hybrid'in 1.
        sonucunu koruyordu, ama gerçek bir vakada doğru cevap hybrid'in
        3. sırasındaydı (1. sıra reranker sonrası da hayatta kalmıştı, bu
        yüzden eski güvenlik ağı hiç devreye girmedi) — reranker yine de
        3. sırayı tamamen eleyebiliyordu. guard_top_n=3, deneyimle
        bulunan, hem çoğu gerçek "reranker hatası" vakasını yakalayan hem
        de reranker'ın kendi kararına çok fazla müdahale etmeyen bir denge.

        Neden gerekli: cross-encoder reranker, bazı sorgularda hybrid'in
        oybirliğiyle (hem embedding hem BM25) bulduğu güçlü bir sonucu
        tamamen gözden kaçırabiliyor. Bu, reranker'ın "her zaman daha iyi
        karar verir" varsayımına karşı bir güvenlik ağı — projedeki diğer
        "gerekirse otomatik düzelt" katmanlarıyla (chunk_id çakışma
        koruması, robots.txt fail-safe vb.) aynı felsefede.
        """
        reranked = self.rerank(query, candidates, top_k=top_k)
        if not candidates:
            return reranked

        guard_pool = candidates[:guard_top_n]
        reranked_ids = {r["chunk_id"] for r in reranked}
        missing = [c for c in guard_pool if c["chunk_id"] not in reranked_ids]
        if not missing or not reranked:
            return reranked

        # En zayıf reranker sonuçlarından başlayarak, en güçlü kurtarılanı
        # önce yerleştir. len(missing) > len(reranked) olursa taşanlar
        # atlanır (top_k sınırı korunur).
        for i, rescue in enumerate(missing):
            if i >= len(reranked):
                break
            idx_to_replace = len(reranked) - 1 - i
            base_score = min(r["rerank_score"] for r in reranked)
            reranked[idx_to_replace] = {
                **rescue,
                "rerank_score": base_score - i * 1e-6,  # sıralamada teklik için ihmal edilebilir fark
                "rescued_by_safety_net": True,
            }

        reranked.sort(key=lambda c: c["rerank_score"], reverse=True)
        return reranked