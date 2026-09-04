text = open("web/app.py", encoding="utf-8").read()
marker = "rerank_with_safety_net("
idx = text.find(marker)
print(repr(text[idx-50:idx+300]))
