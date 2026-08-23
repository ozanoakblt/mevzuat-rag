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


def turkish_tokenize(text: str) -> list[str]:
    lowered = turkish_lower(text)
    tokens = _TOKEN_RE.findall(lowered)
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]
