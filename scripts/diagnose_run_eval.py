from pathlib import Path

src = Path("scripts/run_eval.py").read_text(encoding="utf-8")

checks = [
    ("A: --resume argparse blogu", """    parser.add_argument(
        "--resume",
        action="store_true",
        help="eval/results.json'daki tamamlanmis sorulari atlayip devam et",
    )
    args = parser.parse_args()"""),
    ("B: results/completed_ids/RESULTS_PATH satirlari", """    results = []
    completed_ids: set[str] = set()
    RESULTS_PATH.parent.mkdir(exist_ok=True)"""),
    ("C: if args.resume satiri", """    if args.resume and RESULTS_PATH.exists():"""),
    ("D: prev_results atamasi", """        prev_results = prev.get("results", [])"""),
    ("E: completed_ids blogu", """        completed_ids = {
            r["id"] for r in prev_results
            if (not args.with_generation) or ("total_citation_count" in r)
        }"""),
    ("F: yorum satirlari", """        # Sadece gercekten tamamlanmis kayitlari tut - ayni id icin eski
        # (farkli moddan kalma) kaydi listede birakip cift satir olusturma."""),
    ("G: results filtrelemesi", """        results = [r for r in prev_results if r["id"] in completed_ids]"""),
    ("H: remaining satiri", """    remaining = [q for q in questions if q["id"] not in completed_ids]"""),
]

for name, snippet in checks:
    print(name, "->", "VAR" if snippet in src else "YOK/FARKLI")
