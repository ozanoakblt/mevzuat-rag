from pathlib import Path
p = Path("src/common/gemini_client.py")
s = p.read_text(encoding="utf-8")
old = """        if resp.status_code == 429:
            last_error_text = resp.text[:500]
            if attempt < max_retries:
                time.sleep(5.0 + attempt * 3.0)
                continue
            raise GeminiError(f"Gemini API hatasi (429): {last_error_text}")
        if resp.status_code != 200:
            raise GeminiError(f"Gemini API hatasi ({resp.status_code}): {resp.text[:500]}")"""
new = """        if resp.status_code in (429, 503):
            # 429 = kota/rate-limit, 503 = "yuksek talep, gecici" sunucu
            # hatasi - ikisi de gecici, tekrar denemeye deger.
            last_error_text = resp.text[:500]
            if attempt < max_retries:
                time.sleep(5.0 + attempt * 3.0)
                continue
            raise GeminiError(f"Gemini API hatasi ({resp.status_code}): {last_error_text}")
        if resp.status_code != 200:
            raise GeminiError(f"Gemini API hatasi ({resp.status_code}): {resp.text[:500]}")"""
assert old in s, "blok bulunamadi - dosyanin guncel halini gonder"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("Tamamlandi: 503 de artik tekrar deniyor.")
