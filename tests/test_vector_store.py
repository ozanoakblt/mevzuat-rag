import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.embedding.vector_store import VectorStore, _clean_metadata

SAMPLE_CHUNK = {
    "chunk_id": "doc1::m1::f1",
    "doc_id": "doc1",
    "madde_kind": "MADDE",
    "madde_no": "1",
    "madde_baslik": "Amaç",
    "bolum": "Genel Hükümler",
    "fikra_no": "1",
    "bent_no": None,
    "section": None,
    "text": "Bu maddenin amacı test etmektir.",
    "embedding_text": "Test Belgesi > MADDE 1 (Amaç): Bu maddenin amacı test etmektir.",
    "amendment_refs": [],
    "scenario_tags": ["baglanti_talebi", "osb_baglantisi"],
}


def test_clean_metadata_serializes_lists_and_drops_none():
    meta = _clean_metadata(SAMPLE_CHUNK)
    assert meta["scenario_tags"] == "baglanti_talebi,osb_baglantisi"
    assert meta["amendment_refs"] == ""
    assert "bent_no" not in meta  # None olduğu için atıldı


def test_upsert_and_query_roundtrip(tmp_path):
    store = VectorStore(persist_dir=tmp_path / "vs")
    chunks = [SAMPLE_CHUNK]
    embeddings = [[1.0, 0.0, 0.0]]
    store.upsert_chunks(chunks, embeddings)

    assert store.count() == 1

    results = store.query([1.0, 0.0, 0.0], n_results=1)
    assert len(results) == 1
    assert results[0]["chunk_id"] == "doc1::m1::f1"
    assert results[0]["metadata"]["doc_id"] == "doc1"
    assert results[0]["metadata"]["scenario_tags"] == "baglanti_talebi,osb_baglantisi"


def test_upsert_mismatched_lengths_raises(tmp_path):
    store = VectorStore(persist_dir=tmp_path / "vs")
    try:
        store.upsert_chunks([SAMPLE_CHUNK], [[1.0], [2.0]])
        assert False, "ValueError bekleniyordu"
    except ValueError:
        pass


def test_upsert_empty_list_is_noop(tmp_path):
    store = VectorStore(persist_dir=tmp_path / "vs")
    store.upsert_chunks([], [])
    assert store.count() == 0
