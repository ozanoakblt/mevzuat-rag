import json
from pathlib import Path

p = Path("eval/eval_set.json")
data = json.loads(p.read_text(encoding="utf-8"))

for q in data["questions"]:
    if q["id"] == "q24":
        q["notes"] = (
            "GUNCELLEME (2026-09-09 dogrulama): Korpus 67 kaynaga buyudukten sonra "
            "bir yonetmelik-bilisim-guvenligi.json eklendi - bu sorunun hala "
            "kapsam-disi olup olmadigi supheye dustu, --with-generation ile "
            "yeniden test edildi. Sonuc: soru HALA GECERLI bir negatif test. "
            "Sistem bu belgede akilli sayac SIFRELEME STANDARTLARINA dair hicbir "
            "spesifik detay olmadigini dogru sekilde tespit etti - belgede sadece "
            "genel bir atif var (bu sistemler [korpusumuzda OLMAYAN, farkli bir] "
            "Enerji Sektorunde Siber Guvenlik Yetkinlik Modeli Yonetmeligine "
            "tabidir). Model bunu UYDURMADAN dogru rapor etti "
            "(correct_low_confidence: True, guard_low_confidence: True, "
            "total_citation_count: 2 ama ikisi de sadece bu genel atfin "
            "kendisiydi, soruyu cevaplamiyordu). Sonuc: korpusta konuyla "
            "YUZEYSEL iliskili bir belge bulunsa da, sorulan spesifik teknik "
            "standartlar hala kapsam disinda - bu, negatif testlerin sadece "
            "hic ilgili belge yok degil, ilgili gorunen ama yetersiz belge var "
            "senaryosunu da dogru yakaladigini kanitliyor."
        )
        break
else:
    raise SystemExit("q24 bulunamadi")

p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("Tamamlandi: q24 notu guncellendi.")
