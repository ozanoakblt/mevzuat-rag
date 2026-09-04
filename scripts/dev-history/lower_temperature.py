import pathlib

p = pathlib.Path("src/generation/answer_generator.py")
text = p.read_text(encoding="utf-8")

old = "    return chat_completion_text(SYSTEM_PROMPT, user_prompt, model=model, max_tokens=max_tokens)"
new = "    return chat_completion_text(SYSTEM_PROMPT, user_prompt, model=model, max_tokens=max_tokens, temperature=0.0)"

if old not in text:
    print("HATA: eslesme bulunamadi.")
else:
    new_text = text.replace(old, new)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili.")
