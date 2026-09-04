text = open("src/common/groq_client.py", encoding="utf-8").read()
idx = text.find("reasoning_effort=None,")
print(repr(text[max(0,idx-150):idx+50]))
