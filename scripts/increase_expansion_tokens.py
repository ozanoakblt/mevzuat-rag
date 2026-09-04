import pathlib

p = pathlib.Path("src/common/groq_client.py")
text = p.read_text(encoding="utf-8")

old = "        max_tokens=200,\n        json_mode=True,"
new = "        max_tokens=350,\n        json_mode=True,"

count = text.count(old)
print("Kac yer eslesti:", count)

if count == 1:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("Basarili.")
else:
    print("HATA, elle kontrol gerekli.")
