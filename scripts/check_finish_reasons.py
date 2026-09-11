import json
data = json.loads(open("eval/results.json", encoding="utf-8").read())
targets = {"q02","q03","q06","q07","q08","q10","q15","q20","q28","q30","q32","q49"}
for r in data["results"]:
    if r["id"] in targets:
        print(r["id"], "-", "finish_reason:", r.get("finish_reason"), "- total_citation_count:", r.get("total_citation_count"), "- ungrounded:", r.get("ungrounded_citation_count"))
