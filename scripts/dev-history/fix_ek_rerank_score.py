import pathlib

p = pathlib.Path("web/app.py")
text = p.read_text(encoding="utf-8")

old = """        if extra_ek_chunks:
            top_chunks = top_chunks + extra_ek_chunks
            existing_ids.update(c["chunk_id"] for c in extra_ek_chunks)"""

new = """        if extra_ek_chunks:
            for c in extra_ek_chunks:
                c.setdefault("rerank_score", 0.0)
            top_chunks = top_chunks + extra_ek_chunks
            existing_ids.update(c["chunk_id"] for c in extra_ek_chunks)"""

count = text.count(old)
print("Kac yer eslesti:", count)

if count == 1:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("Basarili.")
else:
    print("HATA, elle kontrol gerekli.")
