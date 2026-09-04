import pathlib

p = pathlib.Path("src/generation/citation_guard.py")
text = p.read_text(encoding="utf-8")

anchor = '''def _normalize(text: str) -> str:'''

new_helper = '''_TURKISH_NUMBER_WORDS = {
    "sifir": "0", "bir": "1", "iki": "2", "uc": "3", "dort": "4",
    "bes": "5", "alti": "6", "yedi": "7", "sekiz": "8", "dokuz": "9",
    "on": "10", "yirmi": "20", "otuz": "30", "kirk": "40", "elli": "50",
    "altmis": "60", "yetmis": "70", "seksen": "80", "doksan": "90",
    "yuz": "100", "bin": "1000",
}


def _turkish_word_to_number(word: str) -> int | None:
    """
    Basit birlesik Turkce sayi kelimelerini (ornegin 'altmis', 'yuz yirmi',
    'iki yuz') tam sayiya cevirir. Sadece bu projede mevzuat metinlerinde
    goruleun sinirli aralik (0-999 civari mesafe/sure degerleri) icin
    yeterlidir - genel amacli bir sayi ayristirici degildir.
    """
    parts = word.lower().replace("i", "i").split()
    total = 0
    current = 0
    for part in parts:
        val = _TURKISH_NUMBER_WORDS.get(part)
        if val is None:
            return None
        val = int(val)
        if val == 100 or val == 1000:
            current = (current or 1) * val
            total += current
            current = 0
        else:
            current += val
    return total + current if (total or current) else None


def _normalize_turkish_numbers(text: str) -> str:
    """
    Metindeki Turkce yaziyla sayilari (ornegin 'altmis metre', 'yuz yirmi
    gun') rakama cevirir (ornegin '60 metre', '120 gun'). Bu, kaynak
    metinde yaziyla ('doksan gun') yazilan bir sayinin, modelin rakamla
    ('90 gun') yazdigi ayni degerle citation guard tarafindan farkli
    sanilip yanlislikla "dogrulanamadi" olarak isaretlenmesini onler -
    bu, gercek bir halusinasyon degil, sadece yazim bicimi farkidir.
    """
    number_word_pattern = r"\\b(" + "|".join(_TURKISH_NUMBER_WORDS.keys()) + r")(\\s+(" + "|".join(_TURKISH_NUMBER_WORDS.keys()) + r"))*\\b"

    def _replace(match: "re.Match") -> str:
        num = _turkish_word_to_number(match.group(0))
        return str(num) if num is not None else match.group(0)

    return re.sub(number_word_pattern, _replace, text, flags=re.IGNORECASE)


def _normalize(text: str) -> str:'''

if anchor not in text:
    print("HATA: anchor bulunamadi (_normalize tanimi).")
else:
    text = text.replace(anchor, new_helper, 1)

    old_body = '''    return re.sub(r"\\s+", "", text.strip()).lower()'''
    new_body = '''    text = _normalize_turkish_numbers(text)
    return re.sub(r"\\s+", "", text.strip()).lower()'''

    if old_body not in text:
        print("HATA: _normalize govdesi bulunamadi.")
    else:
        text = text.replace(old_body, new_body, 1)
        p.write_text(text, encoding="utf-8")
        print("Basarili.")
