import pathlib

p = pathlib.Path("src/parsing/metadata.py")
text = p.read_text(encoding="utf-8")

old = 'embedding_text=f"{doc_meta.title} > Ek-{ap[\'ek_no\']}: {ap[\'text\'][:300]}",'
new = 'embedding_text=f"{doc_meta.title} > Ek-{ap[\'ek_no\']}: {ap[\'text\']}",'

count = text.count(old)
print("Kac yer eslesti:", count)

if count == 1:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("Basarili.")
else:
    print("HATA, elle kontrol gerekli.")
