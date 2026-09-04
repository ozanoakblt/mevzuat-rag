text = open("web/static/app.js", encoding="utf-8").read()
lines = text.split("\n")
print("\n".join(f"{i}: {l}" for i, l in enumerate(lines[52:78])))
