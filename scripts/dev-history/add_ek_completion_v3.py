import pathlib

p = pathlib.Path("web/app.py")
text = p.read_text(encoding="utf-8")

old = "    try:\n        answer = generate_answer(question, top_chunks, doc_titles=DOC_TITLES)"

new = """    existing_ids = {c["chunk_id"] for c in top_chunks}
    ek_keys_selected = {
        (c["doc_id"], c["madde_no"])
        for c in top_chunks
        if c.get("madde_kind") == "EK"
    }
    if ek_keys_selected:
        extra_ek_chunks = [
            c
            for c in candidates
            if c.get("madde_kind") == "EK"
            and (c["doc_id"], c["madde_no"]) in ek_keys_selected
            and c["chunk_id"] not in existing_ids
        ]
        if extra_ek_chunks:
            top_chunks = top_chunks + extra_ek_chunks
            existing_ids.update(c["chunk_id"] for c in extra_ek_chunks)

    try:
        answer = generate_answer(question, top_chunks, doc_titles=DOC_TITLES)"""

count = text.count(old)
print("Kac yer eslesti:", count)

if count == 1:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("Basarili.")
else:
    print("HATA, elle kontrol gerekli.")
