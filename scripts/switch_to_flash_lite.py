from pathlib import Path
p = Path(".env")
s = p.read_text(encoding="utf-8")
old = "GEMINI_MODEL=gemini-3.6-flash"
new = "GEMINI_MODEL=gemini-3.5-flash-lite"
assert old in s, ".env icinde GEMINI_MODEL satiri bulunamadi"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("GEMINI_MODEL guncellendi: gemini-3.5-flash-lite")
