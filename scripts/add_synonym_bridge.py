from pathlib import Path
p = Path("src/retrieval/tokenizer.py")
s = p.read_text(encoding="utf-8")

old = """_TOKEN_RE = re.compile(r"[a-zçğıöşü0-9]+", re.UNICODE)


def turkish_tokenize(text: str) -> list[str]:
    lowered = turkish_lower(text)
    tokens = _TOKEN_RE.findall(lowered)
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]"""

new = """_TOKEN_RE = re.compile(r"[a-zçğıöşü0-9]+", re.UNICODE)

# Bilinen terim kopruleri: mevzuat dilinde ayni kavram icin kullanilan,
# ama farkli kelime/kokten gelen terim ciftleri. BM25 sadece TAM token
# eslesmesine bakar - sorgu ve belge farkli terimi kullansa bile bu
# sozlukle ayni kanonik token'a indirgenip eslesmeleri saglanir.
#
# BILEREK genel bir stemming/kok bulma algoritmasi KULLANILMADI: hem elle
# yazilmis basit sonek-kesme hem de yerlesik Snowball Turkce stemmer'i
# test ettik, ikisi de tutarsiz cikti (orn. "madde" ve "maddesi" farkli
# koklere iniyor, "tarife" ile "tarifeler" eslesmiyor) - genel bir kurala
# guvenmek recall'i duzeltmek yerine ongorulemeyen yeni hatalar
# yaratabilirdi. Bu yuzden sadece ELLE DOGRULANMIS, dar kapsamli terim
# ciftleri kullaniliyor - risk yok, cunku sadece burada listelenen
# kelimeler etkileniyor.
#
# Yeni bir terim eslesme sorunu (ornegin eval sonuclarinda RECALL-MISS
# olarak fark edilirse) bulunduysa, buraya yeni bir satir eklemek yeterli.
_SYNONYM_BRIDGES: dict[str, str] = {
    "setpoint": "pset",
    "set": "pset",
    "point": "pset",
    "azami": "limit",
    "sınır": "limit",
}


def turkish_tokenize(text: str) -> list[str]:
    lowered = turkish_lower(text)
    tokens = _TOKEN_RE.findall(lowered)
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    return [_SYNONYM_BRIDGES.get(t, t) for t in tokens]"""

assert old in s, "turkish_tokenize fonksiyonu bulunamadi"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("Tamamlandi: terim koprusu eklendi (stemming yok).")
