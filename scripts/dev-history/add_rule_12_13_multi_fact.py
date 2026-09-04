import pathlib

p = pathlib.Path("src/generation/answer_generator.py")
text = p.read_text(encoding="utf-8")

anchor = """11. ZORUNLU TARAMA: Cevabı yazmadan once, sana verilen TUM kaynak
    pasajlari (1'den son numaraya kadar HEPSI) tek tek gozden gecir.
    Soruyla dogrudan ilgili olan HER pasaji cevabina dahil et - sadece
    ilk gordugun veya en belirgin olan 1-2 pasajla yetinme. Bir pasaj
    soruyla ilgili sayisal bir deger, kosul veya istisna iceriyorsa,
    bunu atlaman kabul edilemez bir eksiklik sayilir. Cevabini
    tamamladiktan sonra, kullandigin kaynak numaralarinin, sana verilen
    kaynaklar arasindaki TUM ilgili pasajlari kapsayip kapsamadigini
    tekrar kontrol et."""

replacement = """11. ZORUNLU TARAMA: Cevabı yazmadan once, sana verilen TUM kaynak
    pasajlari (1'den son numaraya kadar HEPSI) tek tek gozden gecir.
    Soruyla dogrudan ilgili olan HER pasaji cevabina dahil et - sadece
    ilk gordugun veya en belirgin olan 1-2 pasajla yetinme.
12. TEK PASAJ ICINDEKI COKLU FAKTLAR: Bir kaynak pasaj TEK CUMLEDE
    birden fazla ayri bilgi iceriyorsa (ornegin hem "adet" hem "guc/kVA"
    hem "kosul" ayni cumlede geciyorsa), bu bilgilerin HEPSINI ayri ayri
    cevabina yansit - pasaji kullanip da icindeki ikinci/ucuncu bir
    sayisal degeri veya sarti atlaman kabul edilemez bir eksikliktir.
    Ornek: kaynak "X en az bir adet Y bulundurmalidir, bunlarin her biri
    en az Z gucunde olmalidir" diyorsa, cevabinda hem "en az bir adet"
    hem "en az Z gucunde" ikisi de ayri ayri yer almali - sadece adet
    bilgisini verip guc bilgisini atlama.
13. Cevabini tamamladiktan sonra, kullandigin her kaynak pasajin
    icindeki TUM sayisal deger ve kosullari (adet, sure, tutar, yuzde,
    guc, mesafe vb.) cevabina ekleyip eklemedigini tekrar kontrol et."""

if anchor not in text:
    print("HATA: anchor bulunamadi.")
else:
    new_text = text.replace(anchor, replacement)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili.")
