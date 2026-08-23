"""
Faz 2: Ham dosyalardan (PDF/DOC/DOCX) düz metin çıkarma.

Çıktı formatı: paragraf başına bir satır olacak şekilde normalize edilmiş
UTF-8 metin. structure_parser.py bu metni satır satır işler.
"""
from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    pass


def extract_text(path: str | Path) -> str:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix == ".docx":
        return _extract_docx(path)
    if suffix == ".doc":
        return _extract_doc_legacy(path)
    raise ExtractionError(f"Desteklenmeyen dosya türü: {suffix} ({path})")


def _extract_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    lines: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        lines.extend(text.splitlines())
    full_text = "\n".join(lines)
    return _fix_pdf_kerning_artifacts(full_text)


def _fix_pdf_kerning_artifacts(text: str) -> str:
    """
    PDF font kerning'i bazen "MADDE" gibi anahtar kelimelerin ortasına
    hatalı boşluk sokabilir (ör. "GEÇİCİ MA DDE 15"). Bu, structure_parser'ın
    madde sınırını kaçırmasına ve içeriğin bir önceki maddeye karışmasına
    yol açar. Bilinen kalıpları burada normalize ediyoruz.
    """
    import re

    return re.sub(r"\bMA\s+DDE\b", "MADDE", text)


def _extract_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


def _find_soffice() -> str:
    """soffice çalıştırılabilir dosyasını bulur (PATH'te değilse Windows'taki
    standart kurulum yollarını da dener)."""
    import shutil

    found = shutil.which("soffice")
    if found:
        return found

    candidates = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for c in candidates:
        if Path(c).exists():
            return c

    raise ExtractionError(
        "LibreOffice (soffice) bulunamadı. Kurulu değilse "
        "https://www.libreoffice.org/download/download/ adresinden kurun, "
        "ardından bilgisayarı/terminali yeniden başlatıp tekrar deneyin."
    )


def _extract_doc_legacy(path: Path) -> str:
    """
    Eski .doc formatı (binary) için LibreOffice headless ile .txt'e çevirir.
    Çıktı genelde Windows-1254 (Türkçe) encoding'inde gelir; UTF-8'e çevrilir.
    """
    soffice = _find_soffice()
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [
                soffice,
                "--headless",
                "--convert-to",
                "txt:Text",
                str(path),
                "--outdir",
                tmpdir,
            ],
            capture_output=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise ExtractionError(
                f"LibreOffice dönüşümü başarısız ({path}): {result.stderr.decode(errors='replace')}"
            )
        txt_path = Path(tmpdir) / (path.stem + ".txt")
        if not txt_path.exists():
            raise ExtractionError(f"Beklenen çıktı dosyası bulunamadı: {txt_path}")
        raw_bytes = txt_path.read_bytes()

    # Encoding tahmini: önce UTF-8 dene, olmazsa Windows-1254 (Türkçe) dene.
    for encoding in ("utf-8", "cp1254", "latin-1"):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ExtractionError(f"Encoding tespit edilemedi: {path}")