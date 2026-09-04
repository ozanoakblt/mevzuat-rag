import pathlib

path = pathlib.Path("src/generation/citation_guard.py")
content = path.read_text(encoding="utf-8", errors="replace")

marker = "def format_guard_warnings"
idx = content.index(marker)

new_func = '''def format_guard_warnings(result: GuardResult) -> str:
    """Kullaniciya gosterilecek uyari metnini uretir (varsa)."""
    warnings = []
    if result.is_low_confidence:
        warnings.append(
            "UYARI - DUSUK GUVEN: Bulunan kaynaklar bu soruyla zayif iliskili "
            "gorunuyor. Bu cevabi temkinli degerlendirin, resmi metni "
            "mutlaka kontrol edin."
        )
    ungrounded = [c for c in result.citation_checks if not c.grounded]
    if ungrounded:
        nums = ", ".join(f"[{c.citation_num}]" for c in ungrounded)
        warnings.append(
            f"UYARI - DOGRULANAMAYAN ALINTI: {nums} numarali referans(lar)in "
            "alintisi, gosterilen kaynak pasajda birebir bulunamadi. Bu "
            "kismi ozellikle resmi metinle karsilastirin."
        )
    return "\\n".join(warnings)
'''

content = content[:idx] + new_func
path.write_text(content, encoding="utf-8")
print("Dosya duzeltildi, yeni uzunluk:", len(content))
