import pathlib

files = [
    "src/generation/answer_generator.py",
    "src/generation/citation_guard.py",
    "src/retrieval/reranker.py",
    "web/app.py",
]

for f in files:
    path = pathlib.Path(f)
    raw = path.read_text(encoding="utf-8-sig")
    try:
        fixed = raw.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        print(f"ATLANDI ({f}): {e}")
        continue
    path.write_text(fixed, encoding="utf-8")
    print(f"DUZELTILDI: {f}")
