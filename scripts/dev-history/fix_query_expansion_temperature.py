import pathlib

p = pathlib.Path("src/retrieval/query_expansion.py")
text = p.read_text(encoding="utf-8")

old = 'result = chat_completion_json(EXPANSION_SYSTEM_PROMPT, question)'
new = 'result = chat_completion_json(EXPANSION_SYSTEM_PROMPT, question, temperature=0.0)'

count = text.count(old)
print("Kac yer eslesti:", count)

if count == 1:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("Basarili.")
else:
    print("HATA, elle kontrol gerekli.")
