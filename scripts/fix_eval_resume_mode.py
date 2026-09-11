from pathlib import Path

PATH = Path("scripts/run_eval.py")
src = PATH.read_text(encoding="utf-8")

old = """        completed_ids = {r["id"] for r in results}"""
new = """        completed_ids = {
            r["id"] for r in results
            if (not args.with_generation) or ("total_citation_count" in r)
        }"""
assert old in src, "beklenen satir bulunamadi - dosyanin guncel halini gonder"
src = src.replace(old, new)

PATH.write_text(src, encoding="utf-8")
print("Duzeltildi.")
