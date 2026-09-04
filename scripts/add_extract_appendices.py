import pathlib

p = pathlib.Path("src/parsing/metadata.py")
text = p.read_text(encoding="utf-8")

# 1) extract_appendices fonksiyonunu parse_and_save'den once ekleyelim
anchor = "def parse_and_save("
if anchor not in text:
    print("HATA: parse_and_save bulunamadi.")
    raise SystemExit(1)

new_func = '''import re as _re

_EK_HEADER_RE = _re.compile(r"^EK[\\s-]?(\\d{1,2})\\b\\s*[:\\-\\u2013]?\\s*(.*)$", _re.IGNORECASE)
_EK_MAX_CHUNK_CHARS = 4000


def extract_appendices(raw_text: str) -> list[dict]:
    """
    Belgenin sonundaki "EK-1", "EK-18" gibi teknik ekleri (tablo, formul,
    baglanti kriterleri vb.) ayri, bagimsiz parcalar olarak cikarir.
    Bunlar madde/fikra/bent yapisina uymadigi icin parse_document()/
    build_chunks() tarafindan hic yakalanmiyordu (gercek bir vakada
    tespit edildi: Elektrik Sebeke Yonetmeligi'nde Ek-1..Ek-24 hicbir
    chunk'a girmemisti). Sadece BASLI BASINA KISA satirlari (baslik
    olma ihtimali yuksek, <80 karakter) sinir kabul ediyoruz - boylece
    cumle icinde gecen "...Ek-18'i..." gibi referanslari yanlislikla
    sinir saymiyoruz.
    """
    lines = raw_text.splitlines()
    boundaries: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        s = line.strip()
        if not s or len(s) >= 80:
            continue
        m = _EK_HEADER_RE.match(s)
        if m:
            boundaries.append((i, m.group(1)))

    appendices: list[dict] = []
    for idx, (line_idx, ek_no) in enumerate(boundaries):
        end = boundaries[idx + 1][0] if idx + 1 < len(boundaries) else len(lines)
        body = "\\n".join(l.strip() for l in lines[line_idx:end] if l.strip())
        if len(body) < 30:
            continue
        if len(body) <= _EK_MAX_CHUNK_CHARS:
            appendices.append({"ek_no": ek_no, "part": None, "text": body})
        else:
            for part_idx, start in enumerate(range(0, len(body), _EK_MAX_CHUNK_CHARS), start=1):
                appendices.append(
                    {
                        "ek_no": ek_no,
                        "part": part_idx,
                        "text": body[start : start + _EK_MAX_CHUNK_CHARS],
                    }
                )
    return appendices


'''

text = text.replace(anchor, new_func + anchor, 1)
p.write_text(text, encoding="utf-8")
print("extract_appendices eklendi.")
