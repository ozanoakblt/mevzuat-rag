import pathlib

p = pathlib.Path("scripts/run_eval.py")
text = p.read_text(encoding="utf-8")

old = 'answer = generate_answer(question["question"], reranked, doc_titles=DOC_TITLES)'
new = 'answer = generate_answer(q_text, reranked, doc_titles=DOC_TITLES)'

count = text.count(old)
print("generate_answer cagrisi - kac yer eslesti:", count)
if count == 1:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("Basarili.")
elif count == 0:
    print("Zaten guncel ya da farkli - kontrol gerekmiyor.")
