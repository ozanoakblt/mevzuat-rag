import pathlib

p = pathlib.Path("README.md")
raw = p.read_text(encoding="utf-8")

MOJIBAKE_MARKERS = ["Ã", "Ä", "Å", "â€"]

lines = raw.split("\n")
fixed_lines = []
fixed_count = 0
for line in lines:
    if any(m in line for m in MOJIBAKE_MARKERS):
        try:
            fixed_line = line.encode("cp1252").decode("utf-8")
            fixed_lines.append(fixed_line)
            fixed_count += 1
        except (UnicodeEncodeError, UnicodeDecodeError):
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

new_raw = "\n".join(fixed_lines)
p.write_text(new_raw, encoding="utf-8")
print(f"Duzeltilen satir sayisi: {fixed_count}")
