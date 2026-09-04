text = open("web/static/app.js", encoding="utf-8").read()
lines = text.split("\n")

def show(keyword, context=1):
    print(f"\n=== '{keyword}' ===")
    for i, line in enumerate(lines):
        if keyword in line:
            start = max(0, i - context)
            end = min(len(lines), i + context + 1)
            for j in range(start, end):
                marker = ">>" if j == i else "  "
                print(f"{marker} {j}: {lines[j]}")

show("function resetSourcePanel")
show("function renderSourcePanel")
show("retryBtn")
show("qaScrollEl.appendChild")
show("renderSourcePanel(data.sources")
