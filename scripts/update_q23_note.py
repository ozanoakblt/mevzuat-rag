import json
from pathlib import Path

p = Path("eval/eval_set.json")
data = json.loads(p.read_text(encoding="utf-8"))

for q in data["questions"]:
    if q["id"] == "q23":
        q["notes"] = (
            "GUNCELLEME (2026-09-09 dogrulama): Korpus 67 kaynaga buyudukten "
            "sonra usul-akilli-sayac.json ve usul-osos.json gibi sayac-ilgili "
            "belgeler eklendi - bu sorunun hala kapsam-disi olup olmadigi "
            "supheye dustu, --with-generation ile yeniden test edildi. "
            "Sonuc: soru HALA GECERLI bir negatif test. Sistem korpusta "
            "sayacla ilgili birkac YAKIN ama TAM EsLESMEYEN hukum buldu "
            "(sayac degisimi/temini, fazla tuketim iadesi, iletim sistemi "
            "sayac tesisi - 4 alinti, hepsi grounded) ama acikca kullanicinin "
            "sayac arizasinda ILK ASAMADA ne yapmasi gerektigi konusunda "
            "yeterli bilgi bulamadim diyerek soruyu cevaplamadigini dogru "
            "sekilde belirtti - UYDURMADI (correct_low_confidence: True, "
            "guard_low_confidence: True). Sonuc: model, ilgili gorunen ama "
            "sorunun ozunu (ariza SURECI) cevaplamayan pasajlari ayirt "
            "edebiliyor - bu, q24teki bulguyla ayni deseni dogruluyor."
        )
        break
else:
    raise SystemExit("q23 bulunamadi")

p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("Tamamlandi: q23 notu guncellendi.")
