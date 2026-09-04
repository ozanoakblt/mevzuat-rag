import pathlib

p = pathlib.Path("src/generation/answer_generator.py")
text = p.read_text(encoding="utf-8")

anchor = """5b. ÖNEMLİ AYRIM: farklı KOŞULLARA bağlı farklı değerler (örn. "50 kW altı
    için X, 50 kW üstü için Y", "meskun mahal içi için A, dışı için B")
    ÇELİŞKİ DEĞİLDİR — bunlar birbirini tamamlayan, farklı senaryolara
    uygulanan kurallardır. Bu durumda "çelişki var" deme; bunun yerine
    HANGİ KOŞULDA HANGİ DEĞERİN geçerli olduğunu net şekilde ayır ve
    listele. Gerçek çelişki, aynı koşul için birbirini DOĞRUDAN
    YALANLAYAN iki farklı değer olduğunda söz konusudur."""

addition = anchor + """
5c. Koşullu değerleri listelerken HER değerin yanına, kaynak metinde
    yazan TAM kriteri (güç eşiği, konum, kullanıcı sayısı vb.) MUTLAKA
    ekle — sadece rakamı verme. Bir değeri diğerinin "genel tavanı",
    "üst sınırı" veya "varsayılanı" gibi sunma; bu, kaynak metinde
    AÇIKÇA öyle yazmıyorsa YANLIŞTIR. Her deger kendi bagimsiz kosuluyla
    birlikte sunulmalı. Ornek DOGRU format:
    "- [Kosul A, ornegin '50 kW alti, meskun mahal ici']: X metre
     - [Kosul B, ornegin '50 kW ustu VEYA meskun mahal disi']: Y metre"
    Bu iki satiri "X metre (taban), Y metre'yi asamaz (tavan)" seklinde
    TEK bir olcek gibi birlestirme - bunlar ayri kosullardir, ayri
    sonuclardir."""

if anchor not in text:
    print("HATA: anchor bulunamadi.")
else:
    new_text = text.replace(anchor, addition)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili.")
