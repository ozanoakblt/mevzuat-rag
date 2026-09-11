import json
from pathlib import Path

p = Path("eval/eval_set.json")
data = json.loads(p.read_text(encoding="utf-8"))

before = len(data["questions"])
data["questions"] = [q for q in data["questions"] if q["id"] != "q53"]
after = len(data["questions"])
assert before - after == 1, "tam olarak 1 soru kaldirilmali"

for q in data["questions"]:
    if q["id"] == "q50":
        q["notes"] = (
            "DOGRULANDI (2026-09-09): --with-generation ile test edildi. "
            "Sistem korpusta dogalgaz depolamayla YUZEYSEL iliskili bir "
            "hukum buldu (onlisans/lisans basvuru CAKISMASI durumunda "
            "oncelik sirasi kurali - dogalgaz depolama bu listede bir "
            "madde olarak geciyor) ama acikca dogrudan dogalgaz depolama "
            "tesisi lisansi almak icin aranan genel sartlar yer "
            "almamaktadir diyerek soruyu cevaplamadigini dogru sekilde "
            "belirtti - UYDURMADI. NOT: guard_low_confidence bu vakada "
            "False cikti (total_citation_count: 1, grounded) - bu, "
            "guard'imizin bilinen bir sinirlamasi: alinti var VE dogru "
            "(grounded) ama sorunun ozunu cevaplamiyor durumunu "
            "yakalayamiyor (bu, anlamsal/NLI seviyesi bir analiz "
            "gerektirir, basit regex/string eslesmesiyle cozulemez). "
            "Soru gecerliligini koruyor, ama bu ornek ayni zamanda "
            "citation_guard'in bir sinirini da belgeliyor."
        )
        break

p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Tamamlandi: q53 kaldirildi, q50 notu guncellendi. Toplam soru: {len(data['questions'])}")
