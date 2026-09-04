import pathlib

p = pathlib.Path("src/common/groq_client.py")
text = p.read_text(encoding="utf-8")

old = '''def chat_completion_text(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.1,
    timeout: float = 60.0,
    max_retries: int = 4,
    max_tokens: int = 1000,
) -> str:'''

new = '''def chat_completion_text(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.1,
    timeout: float = 60.0,
    max_retries: int = 4,
    max_tokens: int = 1000,
    reasoning_effort: str | None = None,
) -> str:'''

if old not in text:
    print("HATA A: fonksiyon imzasi bulunamadi.")
else:
    text = text.replace(old, new)

old2 = '''        # Cevap üretimi daha fazla akıl yürütme gerektirebilir; "low" yerine
        # varsayılanı (None -> API\\'nin kendi varsayılanı) kullanıyoruz.
        reasoning_effort=None,
    )'''

new2 = '''        reasoning_effort=reasoning_effort,
    )'''

if old2 not in text:
    print("HATA B: reasoning_effort=None cagrisi bulunamadi.")
else:
    text = text.replace(old2, new2)

p.write_text(text, encoding="utf-8")
print("Tamamlandi.")
