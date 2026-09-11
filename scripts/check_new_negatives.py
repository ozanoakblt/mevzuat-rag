import json
data = json.loads(open("eval/results.json", encoding="utf-8").read())
targets = {"q50", "q51", "q52", "q53"}
for r in data["results"]:
    if r["id"] in targets:
        print(r["id"], "- correct_low_confidence:", r.get("correct_low_confidence"), "- guard_low_confidence:", r.get("guard_low_confidence"), "- total_citation_count:", r.get("total_citation_count"))
