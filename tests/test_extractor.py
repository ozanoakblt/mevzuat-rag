"""
extractor.py icin testler - ozellikle OCR/text-layer probe davranisi.
"""
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.parsing.extractor import _extract_pdf


def _fake_reader(page_texts: list[str]):
    pages = []
    for text in page_texts:
        page = MagicMock()
        page.extract_text.return_value = text
        pages.append(page)
    reader = MagicMock()
    reader.pages = pages
    return reader


def test_extract_pdf_normal_text_no_warning(caplog):
    reader = _fake_reader(
        ["Bu bir MADDE 1 metnidir, yeterince uzun bir paragraf. " * 3] * 2
    )
    with patch("pypdf.PdfReader", return_value=reader):
        with caplog.at_level("WARNING"):
            text = _extract_pdf(Path("normal.pdf"))
    assert "MADDE" in text
    assert not any("taranmis goruntu" in r.message for r in caplog.records)


def test_extract_pdf_scanned_pdf_triggers_warning(caplog):
    reader = _fake_reader(["", "", ""])
    with patch("pypdf.PdfReader", return_value=reader):
        with caplog.at_level("WARNING"):
            text = _extract_pdf(Path("scanned.pdf"))
    assert text == ""
    assert any("taranmis goruntu" in r.message for r in caplog.records)


def test_extract_pdf_empty_document_no_crash(caplog):
    reader = _fake_reader([])
    with patch("pypdf.PdfReader", return_value=reader):
        with caplog.at_level("WARNING"):
            text = _extract_pdf(Path("empty.pdf"))
    assert text == ""
    assert not any("taranmis goruntu" in r.message for r in caplog.records)
