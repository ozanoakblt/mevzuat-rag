"""
Faz 4: Vektor veritabani katmani (FAISS, yerel/dosya-tabanli, ucretsiz).

Chroma'dan FAISS'e gecildi: chromadb 1.5.9'un persistent HNSW segment
implementasyonu, bu Windows + Python 3.13 ortaminda ~1000+ chunk'lik veri
setlerinde tutarli sekilde "Error loading hnsw index" hatasi veriyor
(kutuphanenin kendi bilinen bir sorunu). FAISS Windows'ta hazir derlenmis
wheel (faiss-cpu) ile geliyor, bu segment/compactor karmasikligi yok,
endustride milyonlarca vektor olceginde kanitlanmis. Public API
(upsert_chunks/query/count) Chroma implementasyonuyla birebir ayni kaldi -
ustteki katmanlarda (hybrid.py, web/app.py) hicbir degisiklik gerekmedi.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np


def _clean_metadata(chunk: dict) -> dict[str, Any]:
    """
    None alanlar atilir, listeler virgul/boru ile ayrilmis string'e cevrilir.
    (Chroma doneminden kalma isim/davranis korunuyor - testler buna bagli.)
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
        self._index_path = self.persist_dir / "index.faiss"
        self._meta_path = self.persist_dir / "metadata.json"

        self._records: dict[int, dict] = {}
        self._chunk_id_to_faiss_id: dict[str, int] = {}
        self._next_id = 0
        self._dim: int | None = None
        self._index: faiss.Index | None = None

        self._load()

    def _load(self) -> None:
        if self._meta_path.exists():
            data = json.loads(self._meta_path.read_text(encoding="utf-8"))
            self._dim = data.get("dim")
            self._next_id = data.get("next_id", 0)
            self._records = {int(k): v for k, v in data.get("records", {}).items()}
            self._chunk_id_to_faiss_id = data.get("chunk_id_to_faiss_id", {})
        if self._index_path.exists() and self._dim is not None:
            self._index = faiss.read_index(str(self._index_path))
        elif self._dim is not None:
            self._index = faiss.IndexIDMap2(faiss.IndexFlatIP(self._dim))

    def _ensure_index(self, dim: int) -> None:
        if self._index is None:
            self._dim = dim
            self._index = faiss.IndexIDMap2(faiss.IndexFlatIP(dim))
        elif self._dim != dim:
            raise ValueError(
                f"Embedding boyutu degisti (mevcut {self._dim}, gelen {dim}) - "
                "vector store'u sifirdan olusturun."
            )

    def _save(self) -> None:
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(self._index_path))
        self._meta_path.write_text(
            json.dumps(
                {
                    "dim": self._dim,
                    "next_id": self._next_id,
                    "records": {str(k): v for k, v in self._records.items()},
                    "chunk_id_to_faiss_id": self._chunk_id_to_faiss_id,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def upsert_chunks(self, chunks: list[dict], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks ve embeddings sayilari eslesmiyor")
        if not chunks:
            return

        dim = len(embeddings[0])
        self._ensure_index(dim)

        vecs = np.array(embeddings, dtype="float32")
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        vecs = vecs / norms

        ids_to_remove = []
        new_ids = []
        for chunk in chunks:
            cid = chunk["chunk_id"]
            if cid in self._chunk_id_to_faiss_id:
                ids_to_remove.append(self._chunk_id_to_faiss_id[cid])
            new_id = self._next_id
            self._next_id += 1
            new_ids.append(new_id)
            self._chunk_id_to_faiss_id[cid] = new_id
            self._records[new_id] = {
                "chunk_id": cid,
                "text": chunk["text"],
                "metadata": _clean_metadata(chunk),
            }

        if ids_to_remove:
            self._index.remove_ids(np.array(ids_to_remove, dtype="int64"))
            for old_id in ids_to_remove:
                self._records.pop(old_id, None)

        self._index.add_with_ids(vecs, np.array(new_ids, dtype="int64"))
        self._save()

    def query(
        self, query_embedding: list[float], n_results: int = 5, where: dict | None = None
    ) -> list[dict]:
        if self._index is None or self._index.ntotal == 0:
            return []

        vec = np.array([query_embedding], dtype="float32")
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        fetch_k = n_results if not where else min(self._index.ntotal, max(n_results * 20, 50))
        scores, ids = self._index.search(vec, fetch_k)

        results = []
        for score, faiss_id in zip(scores[0], ids[0]):
            if faiss_id == -1:
                continue
            record = self._records.get(int(faiss_id))
            if record is None:
                continue
            if where and not all(record["metadata"].get(k) == v for k, v in where.items()):
                continue
            results.append(
                {
                    "chunk_id": record["chunk_id"],
                    "text": record["text"],
                    "metadata": record["metadata"],
                    "distance": float(1.0 - score),
                }
            )
            if len(results) >= n_results:
                break
        return results

    def count(self) -> int:
        return self._index.ntotal if self._index is not None else 0


def load_all_chunks(processed_dir: str | Path) -> list[dict]:
    """data/processed/*.json icindeki tum chunk'lari tek listede toplar."""
    chunks: list[dict] = []
    for path in sorted(Path(processed_dir).glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        chunks.extend(data.get("chunks", []))
    return chunks
