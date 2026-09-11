from pathlib import Path

PATH = Path("scripts/run_eval.py")
src = PATH.read_text(encoding="utf-8")

old = """    if args.resume and RESULTS_PATH.exists():
        prev = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
        results = prev.get("results", [])
        completed_ids = {
            r["id"] for r in results
            if (not args.with_generation) or ("total_citation_count" in r)
        }
        print(f"Resume: {len(completed_ids)}/{len(questions)} soru daha once tamamlanmis, atlaniyor.")"""
new = """    if args.resume and RESULTS_PATH.exists():
        prev = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
        prev_results = prev.get("results", [])
        completed_ids = {
            r["id"] for r in prev_results
            if (not args.with_generation) or ("total_citation_count" in r)
        }
        # Sadece gercekten tamamlanmis kayitlari tut - ayni id icin eski
        # (farkli moddan kalma) kaydi listede birakip cift satir olusturma.
        results = [r for r in prev_results if r["id"] in completed_ids]
        print(f"Resume: {len(completed_ids)}/{len(questions)} soru daha once tamamlanmis, atlaniyor.")"""
assert old in src, "beklenen blok bulunamadi - dosyanin guncel halini gonder"
src = src.replace(old, new)

PATH.write_text(src, encoding="utf-8")
print("Duzeltildi: resume artik cift kayit birakmiyor.")
