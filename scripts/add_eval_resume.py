"""scripts/add_eval_resume.py
run_eval.py'e --resume flag'i ekler: eval/results.json'daki daha once
tamamlanmis sorulari atlayip sadece kalanlari calistirir."""
from pathlib import Path

PATH = Path("scripts/run_eval.py")
src = PATH.read_text(encoding="utf-8")

old_arg = """    parser.add_argument("--with-generation", action="store_true")
    args = parser.parse_args()"""
new_arg = """    parser.add_argument("--with-generation", action="store_true")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="eval/results.json'daki tamamlanmis sorulari atlayip devam et",
    )
    args = parser.parse_args()"""
assert old_arg in src
src = src.replace(old_arg, new_arg)

old_loop_setup = """    results = []
    RESULTS_PATH.parent.mkdir(exist_ok=True)
    for i, q in enumerate(questions, 1):
        print(f"  [{i}/{len(questions)}] {q['id']}: {q['question'][:60]}...")
        results.append(
            run_single_question(q, embedder, vector_store, bm25_index, reranker, args.with_generation)
        )"""
new_loop_setup = """    results = []
    completed_ids: set[str] = set()
    RESULTS_PATH.parent.mkdir(exist_ok=True)
    if args.resume and RESULTS_PATH.exists():
        prev = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
        results = prev.get("results", [])
        completed_ids = {r["id"] for r in results}
        print(f"Resume: {len(completed_ids)}/{len(questions)} soru daha once tamamlanmis, atlaniyor.")

    remaining = [q for q in questions if q["id"] not in completed_ids]
    for i, q in enumerate(remaining, 1):
        print(f"  [{i}/{len(remaining)}] {q['id']}: {q['question'][:60]}...")
        results.append(
            run_single_question(q, embedder, vector_store, bm25_index, reranker, args.with_generation)
        )"""
assert old_loop_setup in src
src = src.replace(old_loop_setup, new_loop_setup)

old_ckpt = """        partial_summary = summarize(results)
        RESULTS_PATH.write_text(
            json.dumps(
                {"summary": partial_summary, "results": results, "completed": i, "total": len(questions)},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )"""
new_ckpt = """        partial_summary = summarize(results)
        RESULTS_PATH.write_text(
            json.dumps(
                {"summary": partial_summary, "results": results, "completed": len(results), "total": len(questions)},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )"""
assert old_ckpt in src
src = src.replace(old_ckpt, new_ckpt)

PATH.write_text(src, encoding="utf-8")
print("run_eval.py guncellendi: --resume eklendi.")
