import pathlib

for filepath in ["web/app.py", "scripts/run_eval.py"]:
    p = pathlib.Path(filepath)
    text = p.read_text(encoding="utf-8")
    old = "for i in range(min(max_len, 20)):"
    new = "for i in range(min(max_len, 13)):"
    count = text.count(old)
    if count == 1:
        text = text.replace(old, new)
        p.write_text(text, encoding="utf-8")
        print(f"{filepath}: geri alindi (13'e donduruldu).")
