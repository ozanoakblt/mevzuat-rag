"""
Faz 4: Vektör veritabanı katmanı (Chroma, yerel/dosya-tabanlı, ücretsiz).

Chroma seçildi çünkü: (1) tamamen yerel, ücretsiz, tek makinede çalışır
(brief madde 2, 3), (2) embedding'lerin yanında metadata'yı da native
saklar — Faz 6'daki hybrid retrieval ve ileride status/scenario_tags'e
göre filtreleme için gerekli, (3) FAISS'e göre kurulum/kullanım daha az
kod gerektirir (MVP için doğru tercih).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import chromadb

COLLECTION_NAME = "mevzuat_chunks"


def _clean_metadata(chunk: dict) -> dict[str, Any]:
    """
    Chroma metadata değerleri sadece str/int/float/bool olabilir (None ve
    liste kabul etmez) — bu yüzden None alanlar atılır, listeler (ör.
    scenario_tags, amendment_refs) virgülle ayrılmış string'e çevrilir.
    """
    meta: dict[str, Any] = {}
    for key in (
        "doc_id",
        "madde_kind",
        "madde_no",
        "madde_baslik",
        "bolum",
        "fikra_no",
        "bent_no",
        "section",
    ):
        val = chunk.get(key)
        if val is not None:
            meta[key] = val
    meta["scenario_tags"] = ",".join(chunk.get("scenario_tags") or [])
    meta["amendment_refs"] = " | ".join(chunk.get("amendment_refs") or [])
    return meta


class VectorStore:
    def __init__(self, persist_dir: str | Path = "data/vector_store"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(self.persist_dir))
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )

    def upsert_chunks(self, chunks: list[dict], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks ve embeddings sayıları eşleşmiyor")
        if not chunks:
            return
        self._collection.upsert(
            ids=[c["chunk_id"] for c in chunks],
            embeddings=embeddings,
            documents=[c["text"] for c in chunks],
            metadatas=[_clean_metadata(c) for c in chunks],
        )

    def query(
        self, query_embedding: list[float], n_results: int = 5, where: dict | None = None
    ) -> list[dict]:
        res = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )
        results = []
        for i in range(len(res["ids"][0])):
            results.append(
                {
                    "chunk_id": res["ids"][0][i],
                    "text": res["documents"][0][i],
                    "metadata": res["metadatas"][0][i],
                    "distance": res["distances"][0][i],
                }
            )
        return results

    def count(self) -> int:
        return self._collection.count()


def load_all_chunks(processed_dir: str | Path) -> list[dict]:
    """data/processed/*.json içindeki tüm chunk'ları tek listede toplar."""
    chunks: list[dict] = []
    for path in sorted(Path(processed_dir).glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        chunks.extend(data.get("chunks", []))
    return chunks
