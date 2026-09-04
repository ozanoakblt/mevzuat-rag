import pathlib

p = pathlib.Path("src/generation/answer_generator.py")
text = p.read_text(encoding="utf-8")

anchor = """10. Cevabının gövdesinde (Kaynak Alıntıları bölümü hariç), kullanıcıya
    kesinlik gerektiren durumlarda resmî metni kontrol etmesini hatırlat.

Cevabını Türkçe, net ve öz yaz."""

replacement = """10. Cevabının gövdesinde (Kaynak Alıntıları bölümü hariç), kullanıcıya
    kesinlik gerektiren durumlarda resmî metni kontrol etmesini hatırlat.
11. ZORUNLU TARAMA: Cevabı yazmadan once, sana verilen TUM kaynak
    pasajlari (1'den son numaraya kadar HEPSI) tek tek gozden gecir.
    Soruyla dogrudan ilgili olan HER pasaji cevabina dahil et - sadece
    ilk gordugun veya en belirgin olan 1-2 pasajla yetinme. Bir pasaj
    soruyla ilgili sayisal bir deger, kosul veya istisna iceriyorsa,
    bunu atlaman kabul edilemez bir eksiklik sayilir. Cevabini
    tamamladiktan sonra, kullandigin kaynak numaralarinin, sana verilen
    kaynaklar arasindaki TUM ilgili pasajlari kapsayip kapsamadigini
    tekrar kontrol et.

Cevabını Türkçe, net ve öz yaz."""

if anchor not in text:
    print("HATA: anchor bulunamadi.")
else:
    new_text = text.replace(anchor, replacement)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili.")
