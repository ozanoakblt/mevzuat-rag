import pathlib

p = pathlib.Path("scripts/run_eval.py")
text = p.read_text(encoding="utf-8")

old = 'EVAL_SET_PATH = ROOT / "eval" / "eval_set_mini.json"  # GECICI: token kotasi icin kucultulmus set'
new = 'EVAL_SET_PATH = ROOT / "eval" / "eval_set.json"'

count = text.count(old)
print("Kac yer eslesti:", count)
if count == 1:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("Geri alindi.")
