import json
data = json.loads(open("eval/results.json", encoding="utf-8").read())
found = False
for r in data["results"]:
    if r["id"] == "q49":
        found = True
        print("BULUNDU, id:", r["id"])
        print("answer_text uzunlugu:", len(r.get("answer_text") or ""))
        print("---CEVAP METNI---")
        print(r.get("answer_text"))
if not found:
    print("q49 results.json icinde bulunamadi!")
