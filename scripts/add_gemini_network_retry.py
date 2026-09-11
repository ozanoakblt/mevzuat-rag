from pathlib import Path
p = Path("src/common/gemini_client.py")
s = p.read_text(encoding="utf-8")

old_import = "import requests"
new_import = "import requests\nfrom requests.exceptions import ConnectionError, Timeout"
assert old_import in s
s = s.replace(old_import, new_import, 1)

old = """    last_error_text = ""
    for attempt in range(max_retries + 1):
        resp = requests.post(
            url,
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
        if resp.status_code in (429, 503):"""
new = """    last_error_text = ""
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                url,
                headers={
                    "x-goog-api-key": api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=timeout,
            )
        except (Timeout, ConnectionError) as network_exc:
            last_error_text = str(network_exc)
            if attempt < max_retries:
                time.sleep(5.0 + attempt * 3.0)
                continue
            raise GeminiError(f"Gemini baglanti hatasi: {last_error_text}") from network_exc

        if resp.status_code in (429, 503):"""
assert old in s, "retry dongusu bulunamadi"
s = s.replace(old, new)

p.write_text(s, encoding="utf-8")
print("Tamamlandi.")
