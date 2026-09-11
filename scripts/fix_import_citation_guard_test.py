from pathlib import Path
p = Path("tests/test_citation_guard.py")
s = p.read_text(encoding="utf-8")
old = "from src.generation.citation_guard import (\n    check_confidence,\n    extract_citation_quotes,\n    format_guard_warnings,\n    run_guard,\n    verify_citations,\n)"
new = "from src.generation.citation_guard import (\n    check_confidence,\n    check_numeric_consistency,\n    extract_citation_quotes,\n    format_guard_warnings,\n    run_guard,\n    verify_citations,\n)"
assert old in s
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("import guncellendi")
