from pathlib import Path
p = Path("scripts/run_eval.py")
s = p.read_text(encoding="utf-8")

old_fn_anchor = """    return summary


def main() -> None:"""
new_fn_anchor = """    return summary


def select_sample(questions: list[dict], n: int) -> list[dict]:
    \"\"\"
    Tam 49 soru yerine, gelistirme dongusunde hizli test icin N sorudan
    olusan dengeli bir alt kume secer. Negatif testlerden en az 1 tane
    (varsa) dahil edilir, kalani difficulty oranina gore bolusturulur.
    Secim deterministiktir - ayni N icin her zaman ayni sorular doner.
    \"\"\"
    if n >= len(questions):
        return questions

    def stride_sample(items: list[dict], k: int) -> list[dict]:
        items = sorted(items, key=lambda q: q["id"])
        if k <= 0:
            return []
        if k >= len(items):
            return items
        step = len(items) / k
        indices = sorted({int(i * step) for i in range(k)})
        return [items[i] for i in indices]

    negatives = [q for q in questions if not q["expected_documents"]]
    positives_by_difficulty: dict[str, list[dict]] = {}
    for q in questions:
        if q["expected_documents"]:
            positives_by_difficulty.setdefault(q["difficulty"], []).append(q)

    n_negatives = 0
    if negatives:
        n_negatives = min(len(negatives), max(1, round(n * len(negatives) / len(questions))))
    n_remaining = n - n_negatives

    result = list(stride_sample(negatives, n_negatives))
    total_positive = sum(len(v) for v in positives_by_difficulty.values())
    allocated = 0
    diff_groups = sorted(positives_by_difficulty.items())
    for idx, (_difficulty, items) in enumerate(diff_groups):
        if idx == len(diff_groups) - 1:
            k = n_remaining - allocated
        elif total_positive:
            k = round(n_remaining * len(items) / total_positive)
        else:
            k = 0
        k = max(0, min(k, len(items)))
        result.extend(stride_sample(items, k))
        allocated += k

    return sorted(result, key=lambda q: q["id"])[:n]


def main() -> None:"""
assert old_fn_anchor in s, "summary/main sinir noktasi bulunamadi"
s = s.replace(old_fn_anchor, new_fn_anchor)

old_arg = """    parser.add_argument(
        \"--ids\",
        type=str,
        default=None,
        help=(
            \"virgulle ayrilmis soru id listesi (ornegin q02,q08,q49) - \"
            \"sadece bu sorulari, tamamlanmis olsalar bile ZORLA yeniden \"
            \"calistirir; results.json'daki diger tum kayitlari degistirmeden \"
            \"birakir. --resume ile birlikte kullanilirsa --ids kazanir.\"
        ),
    )
    args = parser.parse_args()

    eval_data = json.loads(EVAL_SET_PATH.read_text(encoding=\"utf-8\"))
    questions = eval_data[\"questions\"]"""
new_arg = """    parser.add_argument(
        \"--ids\",
        type=str,
        default=None,
        help=(
            \"virgulle ayrilmis soru id listesi (ornegin q02,q08,q49) - \"
            \"sadece bu sorulari, tamamlanmis olsalar bile ZORLA yeniden \"
            \"calistirir; results.json'daki diger tum kayitlari degistirmeden \"
            \"birakir. --resume ile birlikte kullanilirsa --ids kazanir.\"
        ),
    )
    parser.add_argument(
        \"--sample\",
        type=int,
        default=None,
        help=\"Tam sette degil, N sorudan olusan dengeli/deterministik bir alt kumede calistir.\",
    )
    args = parser.parse_args()

    eval_data = json.loads(EVAL_SET_PATH.read_text(encoding=\"utf-8\"))
    questions = eval_data[\"questions\"]
    if args.sample is not None:
        questions = select_sample(questions, args.sample)
        print(f\"Sample modu: {len(questions)} soru secildi ({[q['id'] for q in questions]}).\")"""
assert old_arg in s, "arg parse blogu bulunamadi"
s = s.replace(old_arg, new_arg)

p.write_text(s, encoding="utf-8")
print("Tamamlandi: --sample eklendi.")
