from pathlib import Path
p = Path("src/generation/answer_generator.py")
s = p.read_text(encoding="utf-8")

old = """8. Cevabının SONUNA, kullandığın HER [N] referansı için kaynak pasajdan
   BİREBİR (kelimesi kelimesine, en fazla 20 kelimelik) bir alıntıyı şu
   formatta ekle — bu, iddialarının denetlenebilmesi içindir:
   Kaynak Alıntıları:
   [1]: "pasajdan birebir alınmış kısa alıntı"
   [2]: "pasajdan birebir alınmış kısa alıntı\""""

new = """8. Cevabının SONUNA, kullandığın HER [N] referansı için kaynak pasajdan
   BİREBİR (kelimesi kelimesine, en fazla 20 kelimelik) bir alıntıyı şu
   formatta ekle — bu, iddialarının denetlenebilmesi içindir:
   Kaynak Alıntıları:
   [1]: "pasajdan birebir alınmış kısa alıntı"
   [2]: "pasajdan birebir alınmış kısa alıntı"
8b. ALINTI BIREBIR OLMALI - KISALTMA/DEGISTIRME YOK: alinti icinde "[...]"
    ya da "..." KULLANMA (bir bolumu atlayip kisaltma) - bunun yerine
    pasajdan kesintisiz, tam ve daha kisa bir cumle/cumle parcasi sec.
    Alintiya HICBIR kelime EKLEME veya cikarma (orn. kaynakta "uretim
    tesisinin" yaziyorsa alintida "elektrik uretim tesisinin" yazma - tek
    kelime eklemek bile alintiyi gecersiz kilar). 20 kelimeyi asan bir
    cumleyi tam alintilamak gerekiyorsa, cumlenin TAMAMINI degil, o
    cumlenin icinde birebir gecen, kesintisiz, daha kisa bir alt-parcasini
    sec - cumlenin ortasindan veya sonundan kesintisiz bir parca almak,
    basindan alip sonunu "[...]" ile kesmekten HER ZAMAN daha iyidir."""

assert old in s, "8. kural bulunamadi - dosyanin guncel halini gonder"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("Tamamlandi: 8b kurali eklendi.")
