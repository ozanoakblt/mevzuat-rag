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

APPLICABILITY_SYSTEM_PROMPT = """Sen bir hukuki uygulanabilirlik denetcisisin. Sana bir KULLANICI SORUSU ve bu soruya verilen bir CEVAP (kaynak alintilariyla) verilecek.

Gorevin: cevapta kullanilan hukumlerin/kurallarin, sorudaki SPESIFIK olay/durumla GERCEKTEN ortustugunu kontrol etmek.

Ozellikle su tuzaga dikkat et: cevap, sorudakiyle YUZEYSEL benzer ama ONEMLI bir kosulda (kim sorumlu, hangi taraf kaynakli, hangi kullanici/tesis tipi, hangi olay/sebep, hangi yon/istikamet) FARKLI bir senaryoya ait bir hukmu uyguluyor olabilir.

Ornek UYUMSUZLUK: soru "ariza KULLANICI KAYNAKLI DEGIL" diyor ama cevap "kullanici kaynakli bozulmaya" iliskin sureleri/yukumlulukleri kullaniyor.
Ornek UYUM: soru genel bir "sure nedir" sorusu ve cevap doğrudan o sureyi veren maddeyi kullaniyor.

Eger soru genel/dogrudan bir bilgi talebi ise (vaka/senaryo icermiyor, sadece bir tanim/sure/deger soruyor), bu kontrolun cogu zaman "applicable: true" olmasi beklenir - sadece cevabin ACIKCA farkli bir senaryoyu olaya uyguladigi durumlarda false de.

Sadece su JSON formatinda cevap ver, baska hicbir sey yazma:
{"applicable": true/false, "reason": "kisa (1-2 cumle) gerekce"}"""


@dataclass
class ApplicabilityResult:
    applicable: bool
    reason: str
    checked: bool  # LLM cagrisi basarili oldu mu


def check_applicability(question: str, answer_text: str) -> ApplicabilityResult:
    """
    LLM basarisiz olursa (kota/hata) guard'i BLOKLAMAZ - sessizce
    applicable=True, checked=False doner (fail-open). Bu kontrol bir
    GUVENLIK AGI - kendisi basarisiz olunca sistemin tamamini kilitlememeli,
    citation_guard'daki diger deterministik kontroller zaten calisir.
    """
    user_prompt = f"KULLANICI SORUSU:\n{question}\n\nCEVAP:\n{answer_text}"
    try:
        result = chat_completion_json(APPLICABILITY_SYSTEM_PROMPT, user_prompt, temperature=0.0)
        applicable = result.get("applicable", True)
        reason = str(result.get("reason", "") or "")
        return ApplicabilityResult(applicable=bool(applicable), reason=reason, checked=True)
    except LLMError:
        return ApplicabilityResult(applicable=True, reason="", checked=False)
