import sys
sys.path.insert(0, ".")
from src.generation.citation_guard import _normalize

a = _normalize("Meskun mahal içinde bulunan AG kullanıcısı için altmış metre, birden fazla kullanıcı olması halinde yüz yirmi metreden")
b = _normalize("Meskun mahal içinde bulunan AG kullanıcısı için 60 metre, birden fazla kullanıcı olması halinde 120 metre")
print("Kaynak (yaziyla):", a[:80])
print("Model (rakamla): ", b[:80])
print("Esit mi (60 kismi):", "60metre" in a, "60metre" in b)
