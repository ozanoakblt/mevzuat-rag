import json
data_eval = json.loads(open("eval/eval_set.json", encoding="utf-8").read())
data_res = json.loads(open("eval/results.json", encoding="utf-8").read())
questions_by_id = {q["id"]: q for q in data_eval["questions"]}
targets = {"q02", "q06", "q49"}
for r in data_res["results"]:
    if r["id"] in targets:
        q = questions_by_id[r["id"]]
        print(r["id"], "-", "negatif_test:", not q["expected_documents"], "- correct_low_confidence:", r.get("correct_low_confidence"), "- guard_low_confidence:", r.get("guard_low_confidence"))
        print("   soru:", q["question"])
