import json
from pathlib import Path

data = json.loads(Path("eval/eval_set.json").read_text(encoding="utf-8"))
all_questions = data["questions"]

subset = [q for q in all_questions if q["difficulty"] == "zor" or not q["expected_documents"]]

print(f"Toplam soru: {len(all_questions)}")
print(f"Alt kume (zor + negatif): {len(subset)}")
for q in subset:
    print(" -", q["id"], "|", q["difficulty"], "|", q["question"][:50])

mini_data = {"_schema_note": data["_schema_note"], "questions": subset}
Path("eval/eval_set_mini.json").write_text(
    json.dumps(mini_data, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("\nKaydedildi: eval/eval_set_mini.json")
