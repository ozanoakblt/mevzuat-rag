from pathlib import Path
p = Path("src/generation/citation_guard.py")
s = p.read_text(encoding="utf-8")

old = """def _normalize(text: str) -> str:
    \"\"\"
    Karşılaştırma için: TÜM boşlukları kaldır (sadece tek boşluğa indirmek
    değil), küçük harfe çevir. Neden tüm boşluklar: kaynak PDF'lerde font
    kerning'i kelime ortasına kaçak boşluk sokabiliyor (ör. "işletilmesi"
    -> "işletil mesi" — Faz 2'de "MA DDE" olarak gördüğümüz sorunun aynısı).
    Bu, modelin doğru yazdığı bir alıntının, kaynaktaki tesadüfi bir yazım
    kusuru yüzünden yanlışlıkla "doğrulanamadı" olarak işaretlenmesini
    engeller. Bu yaklaşımın riski çok düşük: iki farklı kelimenin
    birleşip yanlışlıkla eşleşmesi için çok uzun ortak alt diziler
    gerekir, pratikte ihmal edilebilir.
    \"\"\"
    text = _normalize_turkish_numbers(text)
    return re.sub(r"\\s+", "", text.strip()).lower()"""

new = """_TYPOGRAPHIC_VARIANTS = {
    "\\u2019": "'", "\\u2018": "'",
    "\\u201c": '"', "\\u201d": '"',
    "\\u2013": "-", "\\u2014": "-",
}


def _normalize_typography(text: str) -> str:
    \"\"\"
    Kaynak PDF'lerdeki Turkce tipografik kesme isareti (’, ornegin
    "MW’i", "km’den") ile modelin urettigi DUZ kesme isaretini (')
    esitler - LLM'ler metin uretirken bu tipografik karakterleri sik sik
    sadelestirir, bu da aksi halde dogru olan bir alintinin sadece bu
    karakter farkindan "dogrulanamadi" olarak yanlislikla isaretlenmesine
    yol acar.
    \"\"\"
    for variant, canonical in _TYPOGRAPHIC_VARIANTS.items():
        text = text.replace(variant, canonical)
    return text


def _normalize(text: str) -> str:
    \"\"\"
    Karşılaştırma için: TÜM boşlukları kaldır, küçük harfe çevir, ve
    tipografik karakter farklarını esitler.
    \"\"\"
    text = _normalize_turkish_numbers(text)
    text = _normalize_typography(text)
    return re.sub(r"\\s+", "", text.strip()).lower()"""

assert old in s, "_normalize fonksiyonu bulunamadi - dosyanin guncel halini gonder"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("Tamamlandi: tipografik karakter farklari esitlendi.")
