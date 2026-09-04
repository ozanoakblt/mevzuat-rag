import pathlib

p = pathlib.Path("README.md")
raw = p.read_text(encoding="utf-8")

try:
    fixed = raw.encode("cp1252").decode("utf-8")
    p.write_text(fixed, encoding="utf-8")
    print("Basarili. Yeni uzunluk:", len(fixed))
except (UnicodeEncodeError, UnicodeDecodeError) as e:
    print("HATA:", e)
    print("Hata konumu civari:", raw[max(0, e.start-30):e.start+30] if hasattr(e, "start") else "?")
