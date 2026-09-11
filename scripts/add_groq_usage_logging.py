from pathlib import Path
p = Path("src/common/groq_client.py")
s = p.read_text(encoding="utf-8")

old_import = """import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions\""""
new_import = """import requests

from .usage_logger import log_usage

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions\""""
assert old_import in s
s = s.replace(old_import, new_import)

old_return = """        data = resp.json()
        choice = data["choices"][0]
        return choice["message"]["content"], choice.get("finish_reason")"""
new_return = """        data = resp.json()
        usage = data.get("usage") or {}
        log_usage(
            "groq", model,
            usage.get("prompt_tokens"), usage.get("completion_tokens"), usage.get("total_tokens"),
        )
        choice = data["choices"][0]
        return choice["message"]["content"], choice.get("finish_reason")"""
assert old_return in s
s = s.replace(old_return, new_return)

p.write_text(s, encoding="utf-8")
print("Tamamlandi: groq_client.py.")
