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


def turkish_tokenize(text: str) -> list[str]:
    lowered = turkish_lower(text)
    tokens = _TOKEN_RE.findall(lowered)
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    return [_SYNONYM_BRIDGES.get(t, t) for t in tokens]
