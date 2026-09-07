import pathlib

p = pathlib.Path("scripts/run_eval.py")
text = p.read_text(encoding="utf-8")

old = "from src.retrieval.hybrid import hybrid_search"
new = "from src.retrieval.hybrid import hybrid_search\nfrom src.retrieval.query_expansion import expand_query"

count = text.count(old)
print("Import - kac yer eslesti:", count)
if count == 1:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("Basarili.")
