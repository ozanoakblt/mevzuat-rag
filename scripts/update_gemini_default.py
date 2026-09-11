from pathlib import Path
p = Path("src/common/gemini_client.py")
s = p.read_text(encoding="utf-8")
old = 'DEFAULT_MODEL = "gemini-3.6-flash"'
new = 'DEFAULT_MODEL = "gemini-3.5-flash-lite"'
assert old in s, "DEFAULT_MODEL satiri bulunamadi"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("gemini_client.py varsayilan model guncellendi.")
