text = open("web/app.py", encoding="utf-8").read()
idx = text.find("top_chunks = _state")
print(text[max(0,idx-100):idx+500])
