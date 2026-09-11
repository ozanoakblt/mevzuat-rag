from pathlib import Path
p = Path("src/generation/answer_generator.py")
s = p.read_text(encoding="utf-8")

old = """    adlarini birbirinin yerine KULLANMA, birbirinin ESANLAMLISI GIBI
    sunma, ya da biri hakkindaki bilgiyi digerine GENELLEME.

Cevabını Türkçe, net ve öz yaz.\""""

new = """    adlarini birbirinin yerine KULLANMA, birbirinin ESANLAMLISI GIBI
    sunma, ya da biri hakkindaki bilgiyi digerine GENELLEME.
16. SON KONTROL (cevabi yazmayi bitirdikten sonra, gondermeden once yap):
    Cevabinda "dolayisiyla ... yapilamaz", "bu nedenle ... yasaktir",
    "... mumkun degildir" gibi bir YASAKLAYICI/OLUMSUZ sonuc cumlesi
    var mi diye kontrol et. Varsa, kullandigin kaynak pasajlarda bu
    OLUMSUZ sonucu (yasak/imkansizlik) DOGRUDAN ve ACIKCA soyleyen bir
    ifade var mi diye tekrar bak. Kaynaklar sadece FARKLI bir senaryoyu
    (örn. karsi/olumlu durumu) anlatiyorsa ve sen bundan kendi
    cikariminla bir YASAK sonucu turetmissen (kural 2b ihlali), o
    cumleyi SIL ve yerine "mevzuatta bu senaryo icin acik bir hukum
    bulunmuyor, kesin sonuc cikarilamaz" seklinde degistir - "muhtemelen
    yapilamaz" gibi yumusatilmis bir versiyon da YETERLI DEGILDIR, tam
    olarak "hukum yok" demen gerekir.

Cevabını Türkçe, net ve öz yaz.\""""

assert old in s, "kural 15 sonu / kapanis bulunamadi - dosyanin guncel halini gonder"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("Tamamlandi: 16. son-kontrol kurali eklendi.")
