import pathlib

p = pathlib.Path("src/generation/citation_guard.py")
text = p.read_text(encoding="utf-8")

old = '''    has_ungrounded = any(not c.grounded for c in citation_checks)
    return GuardResult(
        is_low_confidence=is_low_confidence or has_ungrounded,
        best_rerank_score=best_score,
        citation_checks=citation_checks,
    )'''

new = '''    has_ungrounded = any(not c.grounded for c in citation_checks)
    has_conflation = detect_institution_conflation(answer_text)
    return GuardResult(
        is_low_confidence=is_low_confidence or has_ungrounded or has_conflation,
        best_rerank_score=best_score,
        citation_checks=citation_checks,
    )'''

count = text.count(old)
print("Kac yer eslesti:", count)

if count == 1:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("Basarili.")
else:
    print("HATA, elle kontrol gerekli.")
