text = open("src/parsing/metadata.py", encoding="utf-8").read()
idx = text.find("chunks = build_chunks(doc_meta, blocks)")
print(repr(text[idx:idx+150]))
