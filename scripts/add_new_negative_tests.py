import json
from pathlib import Path

p = Path("eval/eval_set.json")
data = json.loads(p.read_text(encoding="utf-8"))

new_questions = [
    {
        "id": "q50",
        "question": "Doğalgaz depolama tesisi lisansı almak için hangi şartlar aranır?",
        "expected_documents": [],
        "expected_articles": [],
        "difficulty": "zor",
        "scenario_tag": None,
        "notes": (
            "KASITLI KAPSAM DISI TEST: dogalgaz depolama, EPDK'nin AYRI bir "
            "piyasasi (dogalgaz piyasasi) ve mevzuati kapsaminda - bizim "
            "korpusumuz elektrik piyasasi mevzuatiyla sinirli. Depolama "
            "kelimesi korpusta gecse de (yonetmelik-depolama.json), o "
            "ELEKTRIK depolama tesisleri icin - dogalgaz depolamayla "
            "karistirilmamali. Sistem bu ayrimi dogru yapip uydurmamali."
        ),
    },
    {
        "id": "q51",
        "question": "Nükleer enerji santrali kurulması için hangi kurumdan izin alınır?",
        "expected_documents": [],
        "expected_articles": [],
        "difficulty": "zor",
        "scenario_tag": None,
        "notes": (
            "KASITLI KAPSAM DISI TEST: nukleer enerji lisanslamasi ayri bir "
            "kurumun (Nukleer Duzenleme Kurumu) ve ayri bir kanunun "
            "(Nukleer Enerji Kanunu) yetki alaninda - EPDK elektrik piyasasi "
            "mevzuatinin tamamen disinda. Sistem bunu uydurmadan reddetmeli."
        ),
    },
    {
        "id": "q52",
        "question": "Elektrik faturalarında uygulanan KDV oranı nedir?",
        "expected_documents": [],
        "expected_articles": [],
        "difficulty": "zor",
        "scenario_tag": None,
        "notes": (
            "KASITLI KAPSAM DISI TEST: KDV orani vergi hukuku/Hazine ve "
            "Maliye Bakanligi yetki alaninda, EPDK'nin dogrudan duzenledigi "
            "bir konu degil ve korpusumuzda hicbir kaynak vergi oranlarindan "
            "bahsetmiyor. Tarife tebligleri fiyat/bedel hesaplamalarindan "
            "bahsetse de KDV orani ayri, vergi kanunuyla belirlenen bir "
            "deger - sistem bunu tarife maddeleriyle karistirip "
            "uydurmamali."
        ),
    },
    {
        "id": "q53",
        "question": "Elektrik üretim tesisi kurulması için Çevresel Etki Değerlendirmesi (ÇED) süreci nasıl işler?",
        "expected_documents": [],
        "expected_articles": [],
        "difficulty": "zor",
        "scenario_tag": None,
        "notes": (
            "KASITLI KAPSAM DISI TEST: CED sureci Cevre, Sehircilik ve Iklim "
            "Degisikligi Bakanliginin yetki alaninda (CED Yonetmeligi), "
            "EPDK'nin lisanslama sureciyle iliskili olabilir ama CED "
            "SURECININ KENDISI bizim korpusumuzda duzenlenmiyor. Sistem "
            "lisans basvuru belgeleri hukumlerini CED sureciyle karistirip "
            "uydurmamali."
        ),
    },
]

data["questions"].extend(new_questions)
p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Tamamlandi: {len(new_questions)} yeni negatif test eklendi. Toplam soru: {len(data['questions'])}")
