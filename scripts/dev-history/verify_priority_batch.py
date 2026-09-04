text = open("src/ingestion/sources.py", encoding="utf-8").read()
print("toplam doc_id sayisi:", text.count("doc_id="))
print("yonetmelik-kalite-guncel:", "yonetmelik-kalite-guncel" in text)
print("yonetmelik-kapasite-mekanizmasi:", "yonetmelik-kapasite-mekanizmasi" in text)
