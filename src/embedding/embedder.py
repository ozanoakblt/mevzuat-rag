"""
Faz 4: Embedding modeli sarmalayıcısı.

Model seçimi (brief madde 2, 3): ücretsiz, tek makinede (16 GB RAM) çalışan,
Türkçe'yi destekleyen bir sentence-transformers modeli —
`intfloat/multilingual-e5-base` (~1.1 GB, 768 boyutlu vektör). E5 ailesi
retrieval için özel eğitilmiş; sorgu ve pasaj metinlerine FARKLI önekler
eklenmesi gerekiyor ("query: ..." / "passage: ...") — bunu atlarsanız
kalite belirgin şekilde düşer, bu yüzden bu sarmalayıcı zorunlu kılıyor.
"""
from __future__ import annotations

import os
from typing import Protocol

DEFAULT_MODEL_NAME = "intfloat/multilingual-e5-base"


class EmbeddingModel(Protocol):
    """SentenceTransformer ile aynı arayüz (test'lerde sahte model geçilebilir)."""

    def encode(self, texts: list[str], **kwargs) -> list[list[float]]: ...


def _prefixes_for(model_name: str) -> tuple[str, str]:
    """
    (sorgu_oneki, pasaj_oneki). E5 ailesi onek ZORUNLU kilar; BGE-M3 gibi
    diger modeller onek ISTEMEZ (eklemek kaliteyi dusurur) - bkz.
    scripts/compare_embeddings.py'deki olcum.
    """
    if "e5" in model_name.lower():
        return "query: ", "passage: "
    return "", ""


class Embedder:
    def __init__(self, model: EmbeddingModel | None = None, model_name: str | None = None):
        if model is not None:
            self._model = model
            self._query_prefix, self._passage_prefix = "query: ", "passage: "
        else:
            from sentence_transformers import SentenceTransformer

            name = model_name or os.environ.get("EMBEDDING_MODEL", DEFAULT_MODEL_NAME)
            self._model = SentenceTransformer(name)
            # bge-m3 varsayilan 8192 token'a kadar cikar; chunk'lar <=~450 token,
            # gereksiz bellek/sure harcamamak icin 512'ye sinirla.
            if "e5" not in name.lower():
                self._model.max_seq_length = 512
            self._query_prefix, self._passage_prefix = _prefixes_for(name)

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        """İndekslenecek belge parçaları (chunk) için embedding üretir."""
        prefixed = [f"{self._passage_prefix}{t}" for t in texts]
        return self._encode(prefixed)

    def embed_query(self, text: str) -> list[float]:
        """Kullanıcı sorgusu için embedding üretir (tek vektör)."""
        return self._encode([f"{self._query_prefix}{text}"])[0]

    def _encode(self, texts: list[str]) -> list[list[float]]:
        result = self._model.encode(texts, normalize_embeddings=True)
        # SentenceTransformer numpy array döner; JSON/Chroma uyumlu olsun diye list'e çevir.
        return [list(map(float, vec)) for vec in result]
