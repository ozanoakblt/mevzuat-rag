import pathlib

p = pathlib.Path("src/generation/answer_generator.py")
text = p.read_text(encoding="utf-8")

anchor = """5. Farklı pasajlar birbiriyle çelişiyor gibi görünüyorsa, bunu kullanıcıya
   açıkça bildir, çelişkiyi kendi başına "çöz"meye çalışma."""

addition = """5. Farklı pasajlar birbiriyle çelişiyor gibi görünüyorsa, bunu kullanıcıya
   açıkça bildir, çelişkiyi kendi başına "çöz"meye çalışma.
5b. ÖNEMLİ AYRIM: farklı KOŞULLARA bağlı farklı değerler (örn. "50 kW altı
    için X, 50 kW üstü için Y", "meskun mahal içi için A, dışı için B")
    ÇELİŞKİ DEĞİLDİR — bunlar birbirini tamamlayan, farklı senaryolara
    uygulanan kurallardır. Bu durumda "çelişki var" deme; bunun yerine
    HANGİ KOŞULDA HANGİ DEĞERİN geçerli olduğunu net şekilde ayır ve
    listele. Gerçek çelişki, aynı koşul için birbirini DOĞRUDAN
    YALANLAYAN iki farklı değer olduğunda söz konusudur."""

if anchor not in text:
    print("HATA: anchor bulunamadi, dosya degismedi.")
else:
    new_text = text.replace(anchor, addition)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili, eklendi.")
