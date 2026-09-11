import json
data = json.loads(open("eval/results.json", encoding="utf-8").read())
ids = sorted(r["id"] for r in data["results"])
print("Toplam kayit:", len(ids))
print("ID'ler:", ids)
