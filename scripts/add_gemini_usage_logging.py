from pathlib import Path
p = Path("src/common/gemini_client.py")
s = p.read_text(encoding="utf-8")

old_import = """import requests
from requests.exceptions import ConnectionError, Timeout"""
new_import = """import requests
from requests.exceptions import ConnectionError, Timeout

from .usage_logger import log_usage"""
assert old_import in s
s = s.replace(old_import, new_import)

old_return = """        data = resp.json()
        candidate = data["candidates"][0]
        parts = candidate.get("content", {}).get("parts", [])
        content = "".join(p.get("text", "") for p in parts)
        raw_finish_reason = candidate.get("finishReason")
        finish_reason = _FINISH_REASON_MAP.get(raw_finish_reason, raw_finish_reason)
        return content, finish_reason"""
new_return = """        data = resp.json()
        usage = data.get("usageMetadata") or {}
        log_usage(
            "gemini", model,
            usage.get("promptTokenCount"), usage.get("candidatesTokenCount"), usage.get("totalTokenCount"),
        )
        candidate = data["candidates"][0]
        parts = candidate.get("content", {}).get("parts", [])
        content = "".join(p.get("text", "") for p in parts)
        raw_finish_reason = candidate.get("finishReason")
        finish_reason = _FINISH_REASON_MAP.get(raw_finish_reason, raw_finish_reason)
        return content, finish_reason"""
assert old_return in s
s = s.replace(old_return, new_return)

p.write_text(s, encoding="utf-8")
print("Tamamlandi: gemini_client.py.")
