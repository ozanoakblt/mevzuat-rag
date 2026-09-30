from pathlib import Path
p = Path("scripts/run_eval.py")
s = p.read_text(encoding="utf-8")

old = """    print(f\"\\n{'=' * 60}\\nÖZET\\n{'=' * 60}\")
    for key, value in summary.items():
        if isinstance(value, float):
            print(f\"  {key}: {value:.2%}\")
        else:
            print(f\"  {key}: {value}\")"""

new = """    print(f\"\\n{'=' * 60}\\nÖZET\\n{'=' * 60}\")
    for key, value in summary.items():
        if isinstance(value, float):
            if \"latency\" in key:
                print(f\"  {key}: {value:.3f}s\")
            else:
                print(f\"  {key}: {value:.2%}\")
        else:
            print(f\"  {key}: {value}\")"""

assert old in s, "ozet yazdirma dongusu bulunamadi - dosyanin guncel halini gonder"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("Tamamlandi: gecikme artik yuzde olarak yazdirilmiyor.")
