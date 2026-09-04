text = open("src/parsing/metadata.py", encoding="utf-8").read()
print("Dosya uzunlugu:", len(text), "karakter")
print()
import re
for m in re.finditer(r"^(def |class )\w+", text, re.MULTILINE):
    print(" -", m.group(0))
