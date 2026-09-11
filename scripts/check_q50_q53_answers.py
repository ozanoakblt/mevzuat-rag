import json
data = json.loads(open("eval/results.json", encoding="utf-8").read())
for r in data["results"]:
    if r["id"] in {"q50", "q53"}:
        print("=====", r["id"], "=====")
        print(r.get("answer_text"))
        print()
