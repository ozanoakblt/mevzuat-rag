"""
Faz 2: Mevzuat metnini Bölüm > Madde > Fıkra > Bent hiyerarşisine ayrıştırır.

Brief madde 8: "Öncelik: Madde → Fıkra → Bent. Fixed-token chunking kullanma."
Bu modül regex tabanlı, sezgisel (heuristic) bir ayrıştırıcıdır — Türk
mevzuat metinlerinin yaygın kalıplarına dayanır. Kusursuz değildir; amaç,
%100 doğru bir hukuki ayrıştırıcı değil, RAG için "yeterince iyi" chunk
sınırları üretmektir.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# --- Bölüm başlığı: "BİRİNCİ BÖLÜM", "İKİNCİ BÖLÜM" vb. ---
_BOLUM_ORDINALS = (
    "BİRİNCİ|İKİNCİ|ÜÇÜNCÜ|DÖRDÜNCÜ|BEŞİNCİ|ALTINCI|YEDİNCİ|SEKİZİNCİ|"
    "DOKUZUNCU|ONUNCU"
)
BOLUM_RE = re.compile(rf"^({_BOLUM_ORDINALS})\s+BÖLÜM\s*$")

# --- Madde başlığı satırı: "MADDE 1 – ...", "GEÇİCİ MADDE 4 – ...", "EK MADDE 1- ..." ---
MADDE_RE = re.compile(
    r"^(?:(GEÇİCİ|EK)\s+)?MADDE\s+([0-9]+(?:/[A-ZÇĞİÖŞÜ])?)\s*[-–—]\s*(.*)$"
)

# --- Fıkra: "(1)", "(2)" ... metin içinde, sayı 1-99 ---
FIKRA_RE = re.compile(r"\((\d{1,2})\)\s+")

# --- Bent: "a)", "b)", "aa)", "şş)" ... aynı harfin 1-3 tekrarı + parantez ---
BENT_RE = re.compile(r"(?:(?<=\s)|(?<=^))((?P<letter>[a-zçğıöşü])(?P=letter){0,2})\)\s+")

# --- Değişiklik notasyonu: "(Değişik:RG-...)", "(Ek: ...)", "(Mülga:...)" ---
AMENDMENT_RE = re.compile(r"\((Değişik|Ek|Mülga)\s*:?\s*[^)]*\)")


@dataclass
class BentChunk:
    bent_no: str
    text: str
    amendment_refs: list[str] = field(default_factory=list)


@dataclass
class FikraChunk:
    fikra_no: str
    text: str
    amendment_refs: list[str] = field(default_factory=list)
    bents: list[BentChunk] = field(default_factory=list)


@dataclass
class MaddeBlock:
    madde_no: str  # ör. "1", "12/A"
    madde_kind: str  # "MADDE" | "GEÇİCİ MADDE" | "EK MADDE"
    madde_baslik: str | None  # ör. "Amaç ve kapsam"
    bolum: str | None  # o anki bölüm başlığı
    raw_text: str  # maddenin tüm metni (fıkra öncesi dahil)
    fikralar: list[FikraChunk] = field(default_factory=list)
    trailing_appendix: str | None = None  # bkz. _split_appendix

    @property
    def is_tanimlar(self) -> bool:
        if not self.madde_baslik:
            return False
        return "tanım" in self.madde_baslik.lower()


# Belgenin sonunda madde numarasına bağlı olmayan ekler (tablo, dipnot listesi
# vb.) genelde tamamen büyük harfli, uzun bir başlık satırıyla başlar
# (örn. "6446 SAYILI KANUNUN 16 NCI MADDESİNDEKİ PARA CEZASI ... TABLO").
# Bu satırlar normal cümlelerden farklı olarak neredeyse tamamen büyük harf.
APPENDIX_HEADER_RE = re.compile(r"^[0-9A-ZÇĞİÖŞÜ][0-9A-ZÇĞİÖŞÜ\s\.,\-/'’]{14,}$")


def _split_appendix(body_lines: list[str]) -> tuple[list[str], str | None]:
    """
    body_lines içinde ikinci satırdan itibaren (ilk satır maddenin kendi
    metni olabileceğinden atlanır) büyük-harf başlık kalıbına uyan bir satır
    bulursa, o noktadan itibaren her şeyi "ek" (appendix) olarak ayırır.
    Böylece son maddeye (genelde Yürütme/Yürürlük) sonradan eklenmiş
    tablo/dipnot metinleri karışmaz.
    """
    for idx in range(1, len(body_lines)):
        stripped = body_lines[idx].strip()
        if stripped and APPENDIX_HEADER_RE.match(stripped):
            kept = body_lines[:idx]
            appendix = "\n".join(l for l in body_lines[idx:] if l.strip())
            return kept, appendix or None
    return body_lines, None


_AMENDMENT_HISTORY_DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}\s+tarihli")


def _extract_amendment_history_appendix(block: MaddeBlock) -> None:
    """
    "Yürütme"/"Yürürlük" gibi son maddeler bazen belgenin sonundaki
    "değişiklik tarihçesi" listesine bitişik çıkar — ve bu liste de
    "(1) ... (2) ..." formatında olduğu için normal fıkra numaralandırmasıyla
    AYNI görünür (FIKRA_RE bunu gerçek fıkra sanır). Ayırt edici işaret:
    değişiklik tarihçesi girdileri her zaman bir tarihle başlar
    ("30/7/2016 tarihli ve ..."). İlk fıkra hariç, sonraki TÜM fıkralar bu
    kalıba uyuyorsa, bunlar gerçek fıkra değil ek/tarihçe kabul edilir ve
    trailing_appendix'e taşınır (içerik kaybolmaz, sadece chunk'lanmaz).
    """
    if len(block.fikralar) < 2:
        return
    is_yurutme_like = block.madde_baslik and (
        "yürütme" in block.madde_baslik.lower() or "yürürlük" in block.madde_baslik.lower()
    )
    if not is_yurutme_like:
        return
    rest = block.fikralar[1:]
    if not all(_AMENDMENT_HISTORY_DATE_RE.match(f.text) for f in rest):
        return

    appendix_text = "\n".join(f"({f.fikra_no}) {f.text}" for f in rest)
    block.trailing_appendix = (
        f"{block.trailing_appendix}\n{appendix_text}"
        if block.trailing_appendix
        else appendix_text
    )
    block.fikralar = block.fikralar[:1]
    # full_text/raw_text da tutarlı kalsın diye (madde özeti, Groq
    # etiketleme, vb. bu alanı kullanıyor) sadece gerçek fıkrayı yansıtacak
    # şekilde kısaltıyoruz.
    kept_fikra = block.fikralar[0]
    block.raw_text = f"({kept_fikra.fikra_no}) {kept_fikra.text}"


def _extract_amendment_refs(text: str) -> list[str]:
    return [m.group(0) for m in AMENDMENT_RE.finditer(text)]


def _split_bents(fikra_text: str) -> tuple[str, list[BentChunk]]:
    """Fıkra metnini bentlere ayırır. Bent bulunamazsa ([], orijinal metin) döner."""
    matches = list(BENT_RE.finditer(fikra_text))
    if len(matches) < 2:
        # Tek eşleşme muhtemelen yanlış pozitif (örn. cümle içi rastlantısal
        # "a)" gibi); en az 2 ardışık bent bekliyoruz.
        return fikra_text, []

    intro = fikra_text[: matches[0].start()].strip()
    bents: list[BentChunk] = []
    for i, m in enumerate(matches):
        bent_no = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(fikra_text)
        bent_text = fikra_text[start:end].strip()
        bents.append(
            BentChunk(
                bent_no=bent_no,
                text=bent_text,
                amendment_refs=_extract_amendment_refs(bent_text),
            )
        )
    return intro, bents


def _split_fikralar(madde_text: str) -> list[FikraChunk]:
    matches = list(FIKRA_RE.finditer(madde_text))
    if not matches:
        return []

    fikralar: list[FikraChunk] = []
    for i, m in enumerate(matches):
        fikra_no = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(madde_text)
        fikra_text = madde_text[start:end].strip()
        intro, bents = _split_bents(fikra_text)
        fikralar.append(
            FikraChunk(
                fikra_no=fikra_no,
                text=fikra_text,
                amendment_refs=_extract_amendment_refs(fikra_text),
                bents=bents,
            )
        )
    return fikralar


def parse_document(text: str) -> list[MaddeBlock]:
    """
    Düz metni satır satır tarar; BÖLÜM ve MADDE sınırlarını bulur, her
    maddenin ham metnini toplar, sonra fıkra/bent'e ayırır.

    İki geçişli çalışır: önce tüm BÖLÜM/MADDE satırlarının konumlarını
    bulur, sonra her maddenin gövdesini (bir sonraki sınırdan hemen önceki
    olası başlık satırını hariç tutarak) toplar. Bu, "Kapsam" gibi kısa
    başlık satırlarının bir önceki maddenin gövdesine karışmasını engeller.
    """
    lines = text.splitlines()
    n = len(lines)

    # 1. geçiş: yapısal sınırların (bölüm/madde) satır indekslerini bul.
    boundaries: list[tuple[int, str, tuple]] = []  # (line_idx, kind, match_groups)
    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            continue
        if BOLUM_RE.match(line):
            boundaries.append((idx, "BOLUM", ()))
            continue
        m = MADDE_RE.match(line)
        if m:
            boundaries.append((idx, "MADDE", m.groups()))

    # Bölüm başlıklarını çöz (BÖLÜM satırından sonraki ilk dolu satır).
    bolum_titles: dict[int, str] = {}
    for idx, kind, _ in boundaries:
        if kind != "BOLUM":
            continue
        j = idx + 1
        while j < n and not lines[j].strip():
            j += 1
        if j < n:
            bolum_titles[idx] = lines[j].strip()

    madde_blocks: list[MaddeBlock] = []
    current_bolum: str | None = None
    pending_titles: dict[int, str] = {}  # boundary_line_idx -> başlık metni

    for b_i, (idx, kind, groups) in enumerate(boundaries):
        if kind == "BOLUM":
            current_bolum = bolum_titles.get(idx)
            # Bölüm başlığından sonra, ilk maddeden önce başka bir kısa
            # satır varsa (o maddenin başlığı), onu da yakala.
            title_line_idx = None
            for j in range(idx + 1, n):
                if lines[j].strip():
                    title_line_idx = j
                    break
            if title_line_idx is not None:
                next_boundary_idx = (
                    boundaries[b_i + 1][0] if b_i + 1 < len(boundaries) else n
                )
                k = title_line_idx + 1
                while k < n and not lines[k].strip():
                    k += 1
                if k < next_boundary_idx:
                    candidate = lines[k].strip()
                    if candidate and len(candidate) < 80 and not candidate.endswith(
                        (".", ";", ":", ",")
                    ):
                        pending_titles[next_boundary_idx] = candidate
            continue

        kind_prefix, madde_no, rest = groups
        madde_kind = f"{kind_prefix} MADDE" if kind_prefix else "MADDE"

        # Gövde aralığı: bu sınırdan bir sonraki sınıra kadar.
        next_idx = boundaries[b_i + 1][0] if b_i + 1 < len(boundaries) else n
        body_lines = [rest] + lines[idx + 1 : next_idx]

        # Sondaki olası başlık satırını (bir sonraki maddenin başlığı) ayır:
        # boş olmayan son satır, kısa (<80 char) ve cümle gibi bitmiyorsa
        # başlık say, gövdeden çıkar. SADECE bu maddeden sonra gerçekten
        # başka bir sınır (madde/bölüm) varsa yapılır — yoksa (bu belgenin
        # son maddesiyse) çıkarılan "başlık" hiçbir maddeye atanamaz ve
        # içerik sessizce kaybolur (gerçek bir vakada bulunan hata).
        has_next_boundary = b_i + 1 < len(boundaries)
        pending_title: str | None = None
        while body_lines and not body_lines[-1].strip():
            body_lines.pop()
        if has_next_boundary and body_lines:
            last = body_lines[-1].strip()
            if last and len(last) < 80 and not last.endswith((".", ";", ":", ",")):
                pending_title = last
                body_lines = body_lines[:-1]

        # Belge sonu ekleri (tablo/dipnot listesi) varsa ayır — bkz. _split_appendix.
        body_lines, trailing_appendix = _split_appendix(body_lines)

        raw_text = " ".join(l.strip() for l in body_lines if l.strip())
        block = MaddeBlock(
            madde_no=madde_no,
            madde_kind=madde_kind,
            madde_baslik=pending_titles.get(idx),
            bolum=current_bolum,
            raw_text=raw_text,
            trailing_appendix=trailing_appendix,
        )
        block.fikralar = _split_fikralar(raw_text)
        _extract_amendment_history_appendix(block)
        _extract_amendment_history_appendix(block)
        madde_blocks.append(block)

        if pending_title is not None and b_i + 1 < len(boundaries):
            pending_titles[boundaries[b_i + 1][0]] = pending_title

    return madde_blocks
