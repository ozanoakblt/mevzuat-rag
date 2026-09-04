import pathlib

p = pathlib.Path("src/generation/answer_generator.py")
text = p.read_text(encoding="utf-8")

old = "    max_tokens: int = 1800,"
new = "    max_tokens: int = 2500,"

if old not in text:
    print("HATA: eslesme bulunamadi.")
else:
    new_text = text.replace(old, new)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili.")
