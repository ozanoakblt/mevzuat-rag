import pathlib

p = pathlib.Path("src/generation/answer_generator.py")
text = p.read_text(encoding="utf-8")

anchor = """14. ONEMLI AYRIM (11-13 ile 5b-5c CELISMEZ): Kural 11-13, bir pasaji
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

replacement = anchor + """
15. KURUM ADLARINI KESINLIKLE KARISTIRMA: Turkiye elektrik sektorunde
    TEIAS (iletim sistemi isletmecisi, tek ve devlete ait), dagitim
    sirketleri (bolgesel, cok sayida, genelde ozel sektor), EPDK
    (duzenleyici kurum), gorevli tedarik sirketi ve tedarik sirketleri
    BIRBIRINDEN TAMAMEN FARKLI, AYRI tuzel kisilerdir. Kaynak pasajda
    "TEIAS" geciyorsa cevabinda "dagitim sirketi" ile ESITLEME veya
    "dagitim sirketi (TEIAS)" gibi parantezli birlestirme YAPMA - bu
    ciddi bir dogruluk hatasidir. Eger soru dagitim sirketleri hakkindaysa
    ama kaynak pasaj sadece TEIAS'tan bahsediyorsa, bunu ACIKCA belirt:
    "Kaynakta bu yetki TEIAS'a atfediliyor, dagitim sirketleri icin ayni
    yetkinin var olup olmadigi bu pasajlarda belirtilmiyor" gibi. Kurum
    adlarini birbirinin yerine KULLANMA, birbirinin ESANLAMLISI GIBI
    sunma, ya da biri hakkindaki bilgiyi digerine GENELLEME."""

if anchor not in text:
    print("HATA: anchor bulunamadi.")
else:
    new_text = text.replace(anchor, replacement)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili.")
