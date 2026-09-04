import pathlib

p = pathlib.Path("src/generation/citation_guard.py")
text = p.read_text(encoding="utf-8")

anchor = "def run_guard(answer_text: str, chunks: list[dict]) -> GuardResult:"

new_func = '''import re as _re

_INSTITUTION_CONFLATION_RE = _re.compile(
    r"(dağıtım\\s+şirket\\w*|TEİAŞ|EPDK)\\s*\\((dağıtım\\s+şirket\\w*|TEİAŞ|EPDK)\\)",
    _re.IGNORECASE,
)


def detect_institution_conflation(answer_text: str) -> bool:
    """
    Modelin farkli kurumlari (TEIAS, dagitim sirketi, EPDK) birbirinin
    esanlamlisi gibi sunmasini tespit eder - ornegin "dagitim sirketi
    (TEIAS)" gibi bir ifade, bu iki AYRI tuzel kisiyi yanlislikla
    esitleme anlamina gelir (gercek bir vakada tespit edildi: model
    "Dagitim sirketinin (TEIAS) SCADA sistemi..." diye yazmisti, oysa
    kaynak metin sadece TEIAS'tan bahsediyordu, dagitim sirketinden
    hic bahsetmiyordu). Prompt kurali (kural 15) bunu her zaman
    onleyemedigi icin, kod seviyesinde ek bir guvenlik agi olarak
    eklendi - tespit edilirse otomatik dusuk guven tetiklenir.
    """
    for m in _INSTITUTION_CONFLATION_RE.finditer(answer_text):
        a, b = m.group(1).lower(), m.group(2).lower()
        a_norm = "dagitim" if "dağıtım" in a else a
        b_norm = "dagitim" if "dağıtım" in b else b
        if a_norm != b_norm:
            return True
    return False


def run_guard(answer_text: str, chunks: list[dict]) -> GuardResult:'''

if anchor not in text:
    print("HATA: anchor bulunamadi.")
else:
    text = text.replace(anchor, new_func, 1)
    p.write_text(text, encoding="utf-8")
    print("Fonksiyon eklendi.")
