import json
data = json.loads(open("eval/results.json", encoding="utf-8").read())
for r in data["results"]:
    flags = []
    if r.get("is_negative_test"):
        if not r.get("correct_low_confidence"):
            flags.append("NEG-TEST-FAIL")
    else:
        if r.get("recall_hit") is False:
            flags.append("RECALL-MISS")
    total_cit = r.get("total_citation_count")
    ungrounded = r.get("ungrounded_citation_count", 0)
    if total_cit == 0:
        flags.append("NO-CITATIONS")
    elif ungrounded and ungrounded > 0:
        flags.append("UNGROUNDED=" + str(ungrounded) + "/" + str(total_cit))
    if flags:
        rid = r["id"]
        diff = r["difficulty"]
        print(rid + " (" + diff + "): " + ", ".join(flags))
