import json
data = json.loads(open("eval/results.json", encoding="utf-8").read())
for r in data["results"]:
    if r["id"] in {"q02", "q06", "q49"}:
        print(r["id"], "-", "guard_low_confidence:", r.get("guard_low_confidence"), "- total_citation_count:", r.get("total_citation_count"), "- finish_reason:", r.get("finish_reason"))
