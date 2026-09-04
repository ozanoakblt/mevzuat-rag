import pathlib

p = pathlib.Path("src/parsing/metadata.py")
text = p.read_text(encoding="utf-8")

old = 'chunks = build_chunks(doc_meta, blocks)\n\n    out = {'

new = '''chunks = build_chunks(doc_meta, blocks)

    appendix_records = extract_appendices(raw_text)
    for i, ap in enumerate(appendix_records):
        suffix = f"-p{ap['part']}" if ap["part"] else ""
        chunk_id = f"{doc_meta.doc_id}::ek{ap['ek_no']}{suffix}"
        chunks.append(
            ChunkRecord(
                chunk_id=chunk_id,
                doc_id=doc_meta.doc_id,
                madde_kind="EK",
                madde_no=f"Ek-{ap['ek_no']}",
                madde_baslik=None,
                bolum=None,
                fikra_no=None,
                bent_no=None,
                section="Ek",
                text=ap["text"],
                embedding_text=f"{doc_meta.title} > Ek-{ap['ek_no']}: {ap['text'][:300]}",
            )
        )

    out = {'''

count = text.count(old)
print("Kac yer eslesti:", count)

if count == 1:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("Basarili.")
else:
    print("HATA, elle kontrol gerekli.")
