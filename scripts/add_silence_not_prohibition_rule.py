from pathlib import Path
p = Path("src/generation/answer_generator.py")
s = p.read_text(encoding="utf-8")

old = """2. Verilen pasajlar soruyu cevaplamıyorsa veya yetersizse, bunu AÇIKÇA
   belirt ("Verilen kaynaklarda bu konuda yeterli bilgi bulamadım" gibi).
   Zorla bir cevap uydurma."""

new = """2. Verilen pasajlar soruyu cevaplamıyorsa veya yetersizse, bunu AÇIKÇA
   belirt ("Verilen kaynaklarda bu konuda yeterli bilgi bulamadım" gibi).
   Zorla bir cevap uydurma.
2b. SESSIZLIK BIR YASAK/IZIN ANLAMINA GELMEZ: Kaynak pasaj SADECE belirli
    bir senaryoyu duzenliyorsa (orn. "hat kurulduğunda X sureci isler"),
    bu, sorulan TERS/FARKLI senaryo (orn. hat kurulmadiginda) icin "bu
    yapilamaz" ya da "bu yasaktir" SONUCUNA ULASMANI hakli KILMAZ.
    Kaynagin SADECE duzenledigi senaryoyu anlattigini, sorulan farkli
    senaryo hakkinda HICBIR SEY SOYLEMEDIGINI acikca belirt - "bu konuda
    hukum yok, dolayisiyla yapilamaz" diye KENDI mantiksal cikarimini
    YAPMA. Bu, kaynakta olmayan bir bilgiyi (bir YASAK hukmu) sen
    EKLEMEN anlamina gelir ve kural 1'i ihlal eder. Dogru format ornegi:
    "Kaynaklar sadece [senaryo A, sorulmayan] durumunu duzenliyor;
    [senaryo B, sorulan] icin mevzuatta acik bir hukum bulunmuyor - bu
    nedenle 'yapilabilir' ya da 'yapilamaz' seklinde kesin bir sonuc
    cikarilamaz, resmi teyit gerekir." """

assert old in s, "kural 2 bulunamadi - dosyanin guncel halini gonder"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("Tamamlandi: 2b kurali eklendi.")
