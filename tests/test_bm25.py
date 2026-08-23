import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.retrieval.bm25_index import BM25Index
from src.retrieval.tokenizer import turkish_lower, turkish_tokenize


def test_turkish_lower_handles_dotted_i():
    assert turkish_lower("İletim") == "iletim"


def test_turkish_lower_handles_dotless_i():
    assert turkish_lower("Iletim") == "ıletim"


def test_tokenize_removes_stopwords():
    tokens = turkish_tokenize("Bu bir bağlantı anlaşması için gereklidir")
    assert "bu" not in tokens
    assert "bir" not in tokens
    assert "için" not in tokens
    assert "bağlantı" in tokens
    assert "anlaşması" in tokens


def test_tokenize_lowercases_turkish_correctly():
    tokens = turkish_tokenize("İLETİM Sistemi")
    assert "iletim" in tokens
    assert "sistemi" in tokens


CHUNKS = [
    {
        "chunk_id": "d1::m1",
        "doc_id": "d1",
        "madde_no": "1",
        "fikra_no": None,
        "bent_no": None,
        "madde_baslik": "Sayaç arızası",
        "text": "Sayaç arızası durumunda kullanıcı dağıtım şirketine başvurur.",
        "embedding_text": "Test > MADDE 1: Sayaç arızası durumunda kullanıcı dağıtım şirketine başvurur.",
    },
    {
        "chunk_id": "d1::m2",
        "doc_id": "d1",
        "madde_no": "2",
        "fikra_no": None,
        "bent_no": None,
        "madde_baslik": "Bağlantı ücreti",
        "text": "Bağlantı ücreti tarifeye göre belirlenir.",
        "embedding_text": "Test > MADDE 2: Bağlantı ücreti tarifeye göre belirlenir.",
    },
    {
        "chunk_id": "d1::m3",
        "doc_id": "d1",
        "madde_no": "3",
        "fikra_no": None,
        "bent_no": None,
        "madde_baslik": "Tarife değişikliği",
        "text": "Tarife değişikliği talebi yazılı olarak yapılır.",
        "embedding_text": "Test > MADDE 3: Tarife değişikliği talebi yazılı olarak yapılır.",
    },
    {
        "chunk_id": "d1::m4",
        "doc_id": "d1",
        "madde_no": "4",
        "fikra_no": None,
        "bent_no": None,
        "madde_baslik": "Kesinti tazminatı",
        "text": "Kesinti süresi aşıldığında tazminat ödenir.",
        "embedding_text": "Test > MADDE 4: Kesinti süresi aşıldığında tazminat ödenir.",
    },
]


def test_bm25_finds_exact_term_match():
    index = BM25Index(CHUNKS)
    results = index.search("sayaç arızası", top_k=5)
    assert len(results) >= 1
    assert results[0]["chunk_id"] == "d1::m1"


def test_bm25_returns_empty_for_no_match():
    index = BM25Index(CHUNKS)
    results = index.search("alakasız bambaşka bir konu xyzabc", top_k=5)
    assert results == []
