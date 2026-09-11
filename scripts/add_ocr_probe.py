from pathlib import Path
p = Path("src/parsing/extractor.py")
s = p.read_text(encoding="utf-8")

old = """def _extract_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    lines: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or \"\"
        lines.extend(text.splitlines())
    full_text = \"\\n\".join(lines)
    return _fix_pdf_kerning_artifacts(full_text)"""

new = """# Sayfa basina bu karakter sayisinin altinda kalirsak, PDF'in gercek bir
# metin katmani olmadigindan supheleniyoruz - taranmis (scanned) bir
# goruntu OCR'siz boyle davranir: sayfalar var ama extract_text() hep
# bos/neredeyse bos doner.
_MIN_AVG_CHARS_PER_PAGE = 20


def _extract_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    lines: list[str] = []
    total_chars = 0
    for page in reader.pages:
        text = page.extract_text() or \"\"
        total_chars += len(text)
        lines.extend(text.splitlines())
    full_text = \"\\n\".join(lines)

    page_count = len(reader.pages)
    avg_chars_per_page = (total_chars / page_count) if page_count else 0
    if page_count > 0 and avg_chars_per_page < _MIN_AVG_CHARS_PER_PAGE:
        logger.warning(
            \"%s: sayfa basina ortalama %.1f karakter cikarildi (%d sayfa, \"
            \"toplam %d karakter). Bu, PDF'in taranmis goruntu oldugunu ve \"
            \"gercek metin katmani olmadigini gosterebilir - belge OCR \"
            \"gerektirebilir, aksi halde index'e bos/eksik icerikle girer.\",
            path.name, avg_chars_per_page, page_count, total_chars,
        )

    return _fix_pdf_kerning_artifacts(full_text)"""

assert old in s, "_extract_pdf fonksiyonu bulunamadi"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("Tamamlandi: OCR/text-layer probe eklendi.")
