import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.parsing.metadata import DocumentMetadata, _MAX_EMBEDDING_CHARS, build_chunks
from src.parsing.structure_parser import parse_document

DOC_META = DocumentMetadata(doc_id="test-doc", title="Test Belgesi", doc_type="kanun")

SHORT_BENT_TEXT = """MADDE 4 – (1) Faaliyetler şunlardır:
a) Üretim faaliyeti
b) İletim faaliyeti
c) Dağıtım faaliyeti
"""

LONG_BENT_TEXT = """MADDE 3 – (1) Bu Kanunun uygulanmasında;
a) Bağlantı anlaşması: Bir üretim şirketi, dağıtım şirketi ya da tüketicinin iletim sistemine ya da dağıtım sistemine bağlantı yapması için yapılan genel ve özel hükümleri içeren anlaşmayı,
b) Bakan: Enerji ve Tabii Kaynaklar Bakanını çok daha uzun bir tanım cümlesiyle birlikte,
c) Bakanlık: Enerji ve Tabii Kaynaklar Bakanlığını yine oldukça uzun bir tanım cümlesiyle birlikte,
"""


def test_short_bents_collapsed_into_single_fikra_chunk():
    blocks = parse_document(SHORT_BENT_TEXT)
    chunks = build_chunks(DOC_META, blocks)

    assert len(chunks) == 1
    assert chunks[0].bent_no is None
    assert chunks[0].fikra_no == "1"
    assert "Üretim faaliyeti" in chunks[0].text
    assert "İletim faaliyeti" in chunks[0].text
    assert "Dağıtım faaliyeti" in chunks[0].text


def test_long_bents_still_split_individually():
    blocks = parse_document(LONG_BENT_TEXT)
    chunks = build_chunks(DOC_META, blocks)

    assert len(chunks) == 3
    assert all(c.bent_no is not None for c in chunks)
    assert {c.bent_no for c in chunks} == {"a", "b", "c"}


def test_short_bent_chunk_embedding_text_has_context():
    blocks = parse_document(SHORT_BENT_TEXT)
    chunks = build_chunks(DOC_META, blocks)
    assert "Test Belgesi" in chunks[0].embedding_text
    assert "MADDE 4" in chunks[0].embedding_text


# Gercek bir vakada tespit edildi: embedding modeli 512 token siniriyla
# calisiyor (~4.4 karakter/token Turkce mevzuat metninde) - bu esigin
# uzerindeki bir chunk sessizce kesiliyor, dense retrieval iceriginin
# sonunu hic goremiyor. build_chunks artik oversized chunklari cumle
# sinirlarinda boluyor.
def _make_oversized_madde_text(n_sentences: int) -> str:
    sentence = "Bu cümle test amaçlı yeterince uzun bir örnek cümledir ve tekrarlanacaktır."
    body = " ".join(sentence for _ in range(n_sentences))
    return f"MADDE 5 – (1) {body}\n"


def test_oversized_chunk_is_split_into_multiple_parts():
    text = _make_oversized_madde_text(80)  # ~6000+ karakter, esigi asar
    blocks = parse_document(text)
    chunks = build_chunks(DOC_META, blocks)

    assert len(chunks) > 1
    for c in chunks:
        assert len(c.embedding_text) <= _MAX_EMBEDDING_CHARS
        assert c.madde_no == "5"
        assert c.fikra_no == "1"


def test_oversized_chunk_parts_have_sequential_ids_and_preserve_content():
    text = _make_oversized_madde_text(80)
    blocks = parse_document(text)
    chunks = build_chunks(DOC_META, blocks)

    assert chunks[0].chunk_id.endswith("::p1")
    assert chunks[1].chunk_id.endswith("::p2")
    # icerik kaybi olmamali - tum parcalarin metni birlestirilince
    # orijinal cumleler eksiksiz bulunmali.
    combined = " ".join(c.text for c in chunks)
    assert combined.count("test amaçlı yeterince uzun") == 80


def test_normal_sized_chunk_is_not_split():
    blocks = parse_document(SHORT_BENT_TEXT)
    chunks = build_chunks(DOC_META, blocks)
    assert len(chunks) == 1
    assert "::p1" not in chunks[0].chunk_id
