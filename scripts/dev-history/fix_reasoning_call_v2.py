import pathlib

p = pathlib.Path("src/common/groq_client.py")
text = p.read_text(encoding="utf-8")

old = "reasoning_effort=None,\n    )"
new = "reasoning_effort=reasoning_effort,\n    )"

count = text.count(old)
print("Kac yer eslesti:", count)

if count == 1:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("Basarili.")
else:
    print("HATA: 1 yerine", count, "eslesme var, elle kontrol gerekli.")
