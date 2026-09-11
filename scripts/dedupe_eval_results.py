import json
from pathlib import Path

p = Path("eval/results.json")
data = json.loads(p.read_text(encoding="utf-8"))
results = data["results"]

by_id = {}
for r in results:
    rid = r["id"]
    if rid not in by_id or "total_citation_count" in r:
        by_id[rid] = r

deduped = list(by_id.values())
data["results"] = deduped
data["completed"] = len(deduped)
data["total"] = 49
p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Temizlendi: {len(deduped)} kayit (beklenen 49, 48'i generation'li).")
