import pathlib

p = pathlib.Path("README.md")
text = p.read_text(encoding="utf-8")

anchor = "## Bilinen sınırlar"
if anchor not in text:
    print("HATA: anchor bulunamadi.")
else:
    idx = text.find(anchor)
    insert_point = text.find("\n", idx) + 1
    addition = (
        "- Coklu-kurum (TEIAS / dagitim sirketi / EPDK gibi) icerikli sorularda, "
        "model bazen farkli kurumlari birbirinin esanlamlisi gibi sunabiliyor "
        "(orn. \"dagitim sirketi (TEIAS)\"). Kod seviyesinde bir tespit mekanizmasi "
        "(detect_institution_conflation) bu durumlarda otomatik dusuk guven "
        "tetikliyor, ama icerik yine de dikkatli okunmali - ozellikle teknik/"
        "operasyonel (SCADA, set-point, PPC gibi) konularda.\n"
    )
    new_text = text[:insert_point] + addition + text[insert_point:]
    p.write_text(new_text, encoding="utf-8")
    print("Basarili.")
