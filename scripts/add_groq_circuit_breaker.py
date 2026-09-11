from pathlib import Path
p = Path("src/common/groq_client.py")
s = p.read_text(encoding="utf-8")

old = """class GroqError(Exception):
    pass


def _request("""
new = """class GroqError(Exception):
    pass


_rate_limited_until: float = 0.0


def _request("""
assert old in s, "GroqError/_request sinir noktasi bulunamadi"
s = s.replace(old, new)

old2 = """    model = model or os.environ.get(\"GROQ_MODEL\", DEFAULT_MODEL)

    payload = {"""
new2 = """    global _rate_limited_until
    if time.time() < _rate_limited_until:
        remaining = _rate_limited_until - time.time()
        raise GroqError(
            f\"Groq oncesinde bilinen kota asimi hala gecerli (~{remaining:.0f}s \"
            \"kaldi) - gercek istek gonderilmeden atlaniyor.\"
        )

    model = model or os.environ.get(\"GROQ_MODEL\", DEFAULT_MODEL)

    payload = {"""
assert old2 in s, "model atama satiri bulunamadi"
s = s.replace(old2, new2)

old3 = """        if resp.status_code == 429:
            wait_s = _parse_retry_wait_seconds(resp.text) or 5.0
            if attempt < max_retries:
                time.sleep(wait_s + 0.5)
                continue"""
new3 = """        if resp.status_code == 429:
            wait_s = _parse_retry_wait_seconds(resp.text) or 5.0
            _rate_limited_until = time.time() + wait_s
            if attempt < max_retries:
                time.sleep(wait_s + 0.5)
                continue"""
assert old3 in s, "429 blogu bulunamadi"
s = s.replace(old3, new3)

p.write_text(s, encoding="utf-8")
print("Tamamlandi: bilinen kota asimi suresince Groq atlaniyor.")
