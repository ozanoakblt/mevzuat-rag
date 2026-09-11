import re
from pathlib import Path

p = Path("src/generation/citation_guard.py")
s = p.read_text(encoding="utf-8")

old_func = """def _normalize_typography(text: str) -> str:"""
new_func = """_AMENDMENT_ANNOTATION_RE = re.compile(
    r\"\\(\\s*(?:Değişik|Ek|Mülga)(?:\\s+ibare)?\\s*:[^)]*\\)\\d*\",
    re.IGNORECASE,
)


def _strip_amendment_annotations(text: str) -> str:
    \"\"\"
    RG kaynakli \"(Değişik:RG-.../...)\", \"(Ek:RG-.../...)\",
    \"(Değişik ibare:RG-.../...)\" gibi degisiklik notlarini - ve bunlara
    PDF cikariminda bazen boslukusuz yapisan artik rakamlari (orn.
    \"(...)1 bentleri\") - metinden temizler. Bu notlar mevzuatin
    SUBSTANCE'i degil, RG referans/gecmis bilgisi; model okunabilir bir
    cevap uretirken bunlari (haklı olarak) atlayabiliyor, bizim birebir
    alinti karsilastirmamiz bunu yanlislikla \"uyusmuyor\" saymamali.
    \"\"\"
    return _AMENDMENT_ANNOTATION_RE.sub(\"\", text)


def _normalize_typography(text: str) -> str:"""
assert old_func in s, "_normalize_typography fonksiyonu bulunamadi"
s = s.replace(old_func, new_func)

old_normalize = """    text = _normalize_turkish_numbers(text)
    text = _normalize_typography(text)
    return re.sub(r\"\\s+\", \"\", text.strip()).lower()"""
new_normalize = """    text = _normalize_turkish_numbers(text)
    text = _normalize_typography(text)
    text = _strip_amendment_annotations(text)
    return re.sub(r\"\\s+\", \"\", text.strip()).lower()"""
assert old_normalize in s, "_normalize donus satiri bulunamadi"
s = s.replace(old_normalize, new_normalize)

p.write_text(s, encoding="utf-8")
print("Tamamlandi: RG degisiklik notlari + artik rakamlar temizleniyor.")
