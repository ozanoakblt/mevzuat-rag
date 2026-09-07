import pathlib

p = pathlib.Path("scripts/run_eval.py")
text = p.read_text(encoding="utf-8")

old = """CANDIDATE_POOL_SIZE = 20
FINAL_TOP_K = 5"""

new = """CANDIDATE_POOL_SIZE = 30
FINAL_TOP_K = 8"""

count = text.count(old)
print("Sabitler - kac yer eslesti:", count)
if count == 1:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("Basarili.")
