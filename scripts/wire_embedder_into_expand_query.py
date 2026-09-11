from pathlib import Path

files_and_replacements = [
    ("scripts/run_eval.py", "sub_queries = expand_query(q_text)", "sub_queries = expand_query(q_text, embedder=embedder)"),
    ("web/app.py", "sub_queries = expand_query(question)", "sub_queries = expand_query(question, embedder=_state[\"embedder\"])"),
]

for filename, old, new in files_and_replacements:
    p = Path(filename)
    s = p.read_text(encoding="utf-8")
    assert old in s, f"{filename}: satir bulunamadi"
    s = s.replace(old, new)
    p.write_text(s, encoding="utf-8")
    print(f"Tamamlandi: {filename}")
