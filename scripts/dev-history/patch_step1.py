import pathlib

p = pathlib.Path("web/static/app.js")
lines = p.read_text(encoding="utf-8").split("\n")

def replace_line(lines, idx, expected_substr, new_line):
    if expected_substr not in lines[idx]:
        print(f"HATA: satir {idx} beklenen icerigi tasimiyor: {lines[idx]!r}")
        return False
    lines[idx] = new_line
    return True

ok = True

# 1) satir 0: currentBlockEl tanimini stageEl'den once ekle
ok &= replace_line(
    lines, 0, "const stageEl",
    'let currentBlockEl = null;\nconst stageEl = document.querySelector(".stage");'
)

# 2) satir 126: cite span'a data-cite ekle
ok &= replace_line(
    lines, 126, "cite\">$1</span>",
    "      html = html.replace(/\\[(\\d+)\\]/g, '<span class=\"cite\" data-cite=\"$1\">$1</span>');"
)

text = "\n".join(lines)
p.write_text(text, encoding="utf-8")
print("Adim 1-2 tamamlandi:", ok)
