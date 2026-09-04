import pathlib
import re

p = pathlib.Path("tests/test_citation_guard.py")
content = p.read_text(encoding="utf-8")

# Herhangi bir "GÃœVEN" iceren assert satirini bul, DUSUK GUVEN ile degistir
content = re.sub(
    r'assert\s+"[^"]*G[ÃÜ][^"]*VEN[^"]*"\s+in\s+warnings',
    'assert "DUSUK GUVEN" in warnings',
    content,
)

# Herhangi bir "DOÄ" ile baslayan assert satirini bul, DOGRULANAMAYAN ALINTI ile degistir
content = re.sub(
    r'assert\s+"DO[^"]*"\s+in\s+warnings',
    'assert "DOGRULANAMAYAN ALINTI" in warnings',
    content,
)

p.write_text(content, encoding="utf-8")
print("Tamamlandi.")
