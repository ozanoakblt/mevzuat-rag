from pathlib import Path
p = Path("src/generation/citation_guard.py")
s = p.read_text(encoding="utf-8")
old = """def run_guard(answer_text: str, chunks: list[dict]) -> GuardResult:
    is_low_confidence, best_score = check_confidence(chunks)
    citation_checks = verify_citations(answer_text, chunks)
    has_ungrounded = any(not c.grounded for c in citation_checks)
    has_conflation = detect_institution_conflation(answer_text)
    return GuardResult(
        is_low_confidence=is_low_confidence or has_ungrounded or has_conflation,
        best_rerank_score=best_score,
        citation_checks=citation_checks,
    )"""
new = """def run_guard(answer_text: str, chunks: list[dict]) -> GuardResult:
    is_low_confidence, best_score = check_confidence(chunks)
    citation_checks = verify_citations(answer_text, chunks)
    # Kaynak pasajlar verilmisken cevapta HIC alinti cikarilamamissa
    # (kural 8'e gore her cevap alinti icermeli), bu kendi basina supheli
    # bir sinyaldir - modelin alinti blogunu sessizce atladigi (gercek bir
    # eksiklik) ya da retrieval'in konuyla ilgisiz ama esik-ustu skorlu bir
    # sonuc bulup modelin "bulamadim" tarzi cevap verdigi (negatif test
    # senaryosu) durumlarinin ikisini de yakalar - her ikisi de kullaniciya
    # dusuk guvenle sunulmali.
    has_no_citations = bool(chunks) and not citation_checks
    has_ungrounded = any(not c.grounded for c in citation_checks)
    has_conflation = detect_institution_conflation(answer_text)
    return GuardResult(
        is_low_confidence=is_low_confidence or has_ungrounded or has_conflation or has_no_citations,
        best_rerank_score=best_score,
        citation_checks=citation_checks,
    )"""
assert old in s, "run_guard fonksiyonu bulunamadi"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("Tamamlandi: sifir-alinti durumu artik dusuk-guven sayiliyor.")
