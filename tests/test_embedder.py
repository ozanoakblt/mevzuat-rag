import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.embedding.embedder import Embedder


class FakeModel:
    """SentenceTransformer arayüzünü taklit eder, gerçek model indirmez."""

    def __init__(self):
        self.last_call_texts: list[str] = []

    def encode(self, texts, **kwargs):
        self.last_call_texts = texts
        # Her metin için, uzunluğuna dayalı basit deterministik bir "vektör".
        return [[float(len(t)), 0.0, 1.0] for t in texts]


def test_embed_passages_adds_passage_prefix():
    fake = FakeModel()
    embedder = Embedder(model=fake)
    embedder.embed_passages(["metin bir", "metin iki"])
    assert fake.last_call_texts == ["passage: metin bir", "passage: metin iki"]


def test_embed_query_adds_query_prefix():
    fake = FakeModel()
    embedder = Embedder(model=fake)
    embedder.embed_query("bağlantı talebi nasıl yapılır")
    assert fake.last_call_texts == ["query: bağlantı talebi nasıl yapılır"]


def test_embed_query_returns_single_vector_not_list_of_vectors():
    fake = FakeModel()
    embedder = Embedder(model=fake)
    result = embedder.embed_query("test")
    assert isinstance(result, list)
    assert isinstance(result[0], float)


def test_embed_passages_returns_list_of_vectors():
    fake = FakeModel()
    embedder = Embedder(model=fake)
    result = embedder.embed_passages(["a", "bb", "ccc"])
    assert len(result) == 3
    assert all(isinstance(v, list) for v in result)
