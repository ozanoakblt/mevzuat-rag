"""
Faz 5: BM25 için Türkçe'ye uygun tokenizer.

Önemli detay: Python'un standart .lower()'ı Türkçe'de YANLIŞ çalışır —
"I".lower() -> "i" olur ama Türkçe'de "I"nın küçüğü "ı"dır, "İ"nin küçüğü
"i"dir. Bunu düzeltmezsek "İletim" ve "Iletim" farklı token'lara ayrılır,
arama kalitesini bozar.
"""
from __future__ import annotations

import re

# Türkçe'de anlam taşımayan, BM25 skorunu gürültüleyen çok sık geçen kelimeler.
# Mevzuat metinlerinde sık geçen ama ayırt edici olmayan bazı kelimeler de eklendi.
STOPWORDS = {
    "bir", "bu", "şu", "o", "ve", "veya", "ile", "için", "gibi", "de", "da",
    "ki", "mi", "mı", "mu", "mü", "ise", "ancak", "fakat", "ama", "çünkü",
    "her", "hiç", "tüm", "bütün", "kadar", "sonra", "önce", "üzere",
    "olan", "olarak", "olup", "olur", "olmak", "olduğu", "olması",
    "ne", "kim", "hangi", "niçin", "neden", "nasıl",
    "yer", "alan", "alır", "içinde", "üzerinde", "göre", "dair", "ilişkin",
    "diğer", "aynı", "başka", "arasında",
    "ve/veya", "en", "daha", "çok", "az",
}


def turkish_lower(text: str) -> str:
    """Türkçe'ye özgü doğru küçük harfe çevirme."""
    text = text.replace("İ", "i").replace("I", "ı")
    return text.lower()


_TOKEN_RE = re.compile(r"[a-zçğıöşü0-9]+", re.UNICODE)

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


# Hukuki referans token'lari. Genel tokenizer "10/A"yi "10" + "a"ya boler ve
# tek karakterli "a"yi (ve tek haneli madde numaralarini, orn. "EK MADDE 5"
# icindeki "5"i) len>1 filtresiyle atar - yani "MADDE 5/A" ile "MADDE 5"
# ya da "EK MADDE 5" ile "MADDE 5" BM25 icin ayirt edilemez hale gelir
# (madde numarasi catismasi, bkz. eval q04). Bu desenler, referansi TEK bir
# ayirt edici token olarak ekler; mevcut parcali token'lar da korunur (bu
# yuzden sadece EK token uretir, hicbir mevcut eslesmeyi kaldirmaz).
_MADDE_REF_RE = re.compile(r"\b(?:(ek|geçici)\s+)?madde\s+(\d+(?:/[a-zçğıöşü])?)(?![a-zçğıöşü0-9])")
_SLASH_NUM_RE = re.compile(r"(?<![a-zçğıöşü0-9/])(\d+/[a-zçğıöşü])(?![a-zçğıöşü0-9])")
_DATE_RE = re.compile(r"(?<![0-9])(\d{1,2})[./](\d{1,2})[./](\d{4})(?![0-9])")


def _legal_reference_tokens(lowered: str) -> list[str]:
    tokens = []
    for m in _MADDE_REF_RE.finditer(lowered):
        prefix = f"{m.group(1)}_" if m.group(1) else ""
        tokens.append(f"{prefix}madde_{m.group(2)}")
    tokens.extend(m.group(1) for m in _SLASH_NUM_RE.finditer(lowered))
    tokens.extend(
        f"{int(d):02d}.{int(mo):02d}.{y}" for d, mo, y in _DATE_RE.findall(lowered)
    )
    return tokens


def turkish_tokenize(text: str) -> list[str]:
    lowered = turkish_lower(text)
    tokens = _TOKEN_RE.findall(lowered)
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    tokens = [_SYNONYM_BRIDGES.get(t, t) for t in tokens]
    return tokens + _legal_reference_tokens(lowered)
