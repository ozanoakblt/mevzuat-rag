from pathlib import Path

src = Path("scripts/run_eval.py").read_text(encoding="utf-8")

pieces = [
    ("results=[]+completed_ids+mkdir", """    results = []
    completed_ids: set[str] = set()
    RESULTS_PATH.parent.mkdir(exist_ok=True)"""),
    ("+ if args.resume", """
    if args.resume and RESULTS_PATH.exists():"""),
    ("+ prev satiri", """
        prev = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))"""),
    ("+ prev_results", """
        prev_results = prev.get("results", [])"""),
    ("+ completed_ids blogu", """
        completed_ids = {
            r["id"] for r in prev_results
            if (not args.with_generation) or ("total_citation_count" in r)
        }"""),
    ("+ yorum satirlari", """
        # Sadece gercekten tamamlanmis kayitlari tut - ayni id icin eski
        # (farkli moddan kalma) kaydi listede birakip cift satir olusturma."""),
    ("+ results filtre", """
        results = [r for r in prev_results if r["id"] in completed_ids]"""),
    ("+ print resume", """
        print(f"Resume: {len(completed_ids)}/{len(questions)} soru daha once tamamlanmis, atlaniyor.")"""),
    ("+ bos satir + remaining", """

    remaining = [q for q in questions if q["id"] not in completed_ids]"""),
]

acc = ""
for name, piece in pieces:
    acc += piece
    print(name, "->", "VAR" if acc in src else "***KIRILDI***")
