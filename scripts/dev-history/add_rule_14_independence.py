import pathlib

p = pathlib.Path("src/generation/answer_generator.py")
text = p.read_text(encoding="utf-8")

anchor = """13. Cevabini tamamladiktan sonra, kullandigin her kaynak pasajin
    icindeki TUM sayisal deger ve kosullari (adet, sure, tutar, yuzde,
    guc, mesafe vb.) cevabina ekleyip eklemedigini tekrar kontrol et."""

replacement = anchor + """
14. ONEMLI AYRIM (11-13 ile 5b-5c CELISMEZ): Kural 11-13, bir pasaji
    ATLAMAMANI ister - bu, o pasajlari birbirine BAGIMLI ya da IC ICE
    gostermen gerektigi anlamina GELMEZ. Farkli kaynak pasajlar farkli,
    BAGIMSIZ senaryolari (kosullari) anlatiyorsa, bunlari cevabinda AYRI
    AYRI, birbirinden BAGIMSIZ maddeler olarak listele. "Bu sinir su
    kosulda gecerlidir, aksi halde diger kosul uygulanir" gibi zincirleme
    bir bagimlilik kurma - sadece kaynak metinde ACIKCA boyle bir
    bagimlilik ifadesi (orn. "asagidaki durum haric", "bu sinirin
    asilmasi halinde") varsa boyle bir bag kur. Ornek DOGRU yaklasim: "A
    durumu icin X, B durumu icin Y, C durumu icin Z gecerlidir" (uc ayri,
    esit agirlikli madde) - YANLIS yaklasim: "digerleri X uygular, ancak
    C durumunda Y gecerlidir" (sanki C, digerlerinin istisnasiymis gibi
    sunmak, kaynak metinde boyle yazmiyorsa)."""

if anchor not in text:
    print("HATA: anchor bulunamadi.")
else:
    new_text = text.replace(anchor, replacement)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili.")
