"""
Faz 10: Uygulanabilirlik kontrolü (applicability / entailment check).

citation_guard.py'deki kontroller tamamen deterministik/regex-tabanlıdır -
bir alıntının kaynakta GERÇEKTEN geçip geçmediğini doğrulayabilir, ama
"bu alıntı GERÇEKTEN bu soruya uygulanıyor mu" sorusunu cevaplayamaz - bu,
anlamsal/NLI seviyesi bir yargı gerektirir, regex'le çözülemez.

Gerçek bir vakada tespit edildi (EPDK sınav testi, Soru 40): sistem doğru
maddeleri biliyordu (23-26 sorularında aynı hükümleri doğru kullanmıştı)
ama bir VAKA sorusunda YANLIŞ hüküm ailesini seçti - "kullanıcı kaynaklı
OLMAYAN teknik kalite sorunu" senaryosuna, "kullanıcı kaynaklı bozulmaya"
ilişkin süreleri/yükümlülükleri uyguladı. Alıntılar birebir doğruydu
(citation_guard bunu görünce sorun yok derdi) ama cevabın MANTIĞI olaya
uygun değildi.

Bu modül, cevap üretildikten sonra AYRI bir LLM çağrısıyla soruyor: "Bu
cevaptaki hükümler, sorudaki SPESİFİK olayla gerçekten örtüşüyor mu, yoksa
YÜZEYSEL benzer ama farklı bir senaryoya mı ait?" — citation_guard'ın
aksine bu kontrol deterministik değildir (bir LLM çağrısı gerektirir),
bu yüzden ayrı bir modülde tutuluyor.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.common.llm_router import LLMError, chat_completion_json

APPLICABILITY_SYSTEM_PROMPT = """Sen bir hukuki uygulanabilirlik denetcisisin. Sana bir KULLANICI SORUSU, bu soruya verilen bir CEVAP (kaynak alintilariyla) ve varsa cevapta kullanilan KAYNAK PASAJLARIN ham metni verilecek.

Gorevin: cevapta kullanilan hukumlerin/kurallarin, sorudaki SPESIFIK olay/durumla GERCEKTEN ortustugunu kontrol etmek. Kaynak pasajlar verilmisse, yargini SADECE cevabin kendi ozetine degil, o ham pasajlarin GERCEKTEN neyi duzenledigine dayandir.

Ozellikle su tuzaga dikkat et: cevap, sorudakiyle YUZEYSEL benzer ama ONEMLI bir kosulda (kim sorumlu, hangi taraf kaynakli, hangi kullanici/tesis tipi, hangi olay/sebep, hangi yon/istikamet) FARKLI bir senaryoya ait bir hukmu uyguluyor olabilir.

Ornek UYUMSUZLUK: soru "ariza KULLANICI KAYNAKLI DEGIL" diyor ama cevap "kullanici kaynakli bozulmaya" iliskin sureleri/yukumlulukleri kullaniyor.
Ornek UYUM: soru genel bir "sure nedir" sorusu ve cevap doğrudan o sureyi veren maddeyi kullaniyor.

Eger soru genel/dogrudan bir bilgi talebi ise (vaka/senaryo icermiyor, sadece bir tanim/sure/deger soruyor), bu kontrolun cogu zaman "applicable: true" olmasi beklenir - sadece cevabin ACIKCA farkli bir senaryoyu olaya uyguladigi durumlarda false de.

Sadece su JSON formatinda cevap ver, baska hicbir sey yazma:
{"applicable": true/false, "reason": "kisa (1-2 cumle) gerekce"}"""


@dataclass
class ApplicabilityResult:
    applicable: bool | None  # None = kontrol hic yapilamadi (LLM hatasi) - "guvenli" varsayilmaz
    reason: str
    checked: bool  # LLM cagrisi basarili oldu mu


def _format_evidence(chunks: list[dict] | None, max_chunks: int = 8) -> str:
    if not chunks:
        return ""
    lines = []
    for i, c in enumerate(chunks[:max_chunks], 1):
        label = f"{c.get('madde_kind', '')} {c.get('madde_no', '')}".strip()
        text = (c.get("text") or "").strip()
        lines.append(f"[{i}] ({label}) {text}")
    return "\n".join(lines)


def check_applicability(
    question: str, answer_text: str, retrieved_chunks: list[dict] | None = None
) -> ApplicabilityResult:
    """
    retrieved_chunks: uygulanabilirlik yargisinin sadece cevap metnindeki
    (LLM'in kendi ozetledigi) alintilara degil, GERCEKTEN kullanilan kaynak
    pasajlarin ham metnine dayanmasi icin verilir - eskiden checker sadece
    (question, answer) goruyordu, yani modelin kendi cevabinin dogrulugunu
    yine modelin kendi cevabina bakarak yargiliyordu (kor nokta).

    LLM basarisiz olursa (kota/hata) guard'i BLOKLAMAZ ama "kontrol edildi
    ve sorun yok" da DEMEZ - applicable=None, checked=False doner. Eskiden
    applicable=True donuyordu (fail-open); bu, "kontrol basarisiz oldu"
    durumunu "kontrol edildi, uygun bulundu" ile ayni gostermenin YANLIS
    guvenlik sinyali verdigi tespit edildi - caginin API katmani bu
    farki confidence_level'a yansitmali (bkz. web/app.py).
    """
    evidence = _format_evidence(retrieved_chunks)
    user_prompt = f"KULLANICI SORUSU:\n{question}\n\nCEVAP:\n{answer_text}"
    if evidence:
        user_prompt += f"\n\nCEVAPTA KULLANILAN KAYNAK PASAJLAR (ham metin):\n{evidence}"
    try:
        result = chat_completion_json(APPLICABILITY_SYSTEM_PROMPT, user_prompt, temperature=0.0)
        applicable = result.get("applicable", True)
        reason = str(result.get("reason", "") or "")
        return ApplicabilityResult(applicable=bool(applicable), reason=reason, checked=True)
    except LLMError:
        return ApplicabilityResult(applicable=None, reason="", checked=False)
