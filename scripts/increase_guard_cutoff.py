import pathlib

p = pathlib.Path("web/app.py")
text = p.read_text(encoding="utf-8")

old = "if i < 5 and cid not in guard_ids:"
new = "if i < 8 and cid not in guard_ids:"

count = text.count(old)
print("Kac yer eslesti:", count)

if count == 1:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("Basarili.")
else:
    print("HATA: beklenmedik eslesme sayisi.")
