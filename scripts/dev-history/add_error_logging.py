import pathlib

p = pathlib.Path("web/app.py")
text = p.read_text(encoding="utf-8")

old = "    answer = generate_answer(question, top_chunks, doc_titles=DOC_TITLES)"
new = """    try:
        answer = generate_answer(question, top_chunks, doc_titles=DOC_TITLES)
    except Exception as exc:
        import traceback
        error_detail = traceback.format_exc()
        with open("last_error.log", "w", encoding="utf-8") as f:
            f.write(error_detail)
        print("=" * 60)
        print("GENERATE_ANSWER HATASI:")
        print(error_detail)
        print("=" * 60)
        raise"""

if old not in text:
    print("HATA: eslesme bulunamadi.")
else:
    new_text = text.replace(old, new)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili.")
