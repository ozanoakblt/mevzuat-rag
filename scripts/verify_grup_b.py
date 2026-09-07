text = open("src/ingestion/sources.py", encoding="utf-8").read()
print("toplam doc_id sayisi:", text.count("doc_id="))
