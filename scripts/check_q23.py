import json
data = json.loads(open("eval/results.json", encoding="utf-8").read())
for r in data["results"]:
    if r["id"] == "q23":
        print("total_citation_count:", r.get("total_citation_count"))
        print("guard_low_confidence:", r.get("guard_low_confidence"))
        print("correct_low_confidence:", r.get("correct_low_confidence"))
        print("---CEVAP---")
        print(r.get("answer_text"))
