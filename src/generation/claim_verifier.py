"""
Faz 15: Claim-level entailment verification.

citation_guard.py'nin alinti dogrulamasi SADECE string-duzeyinde calisir:
"[N]: '...'" alintisi, chunks[N-1]'in metninde BIREBIR geciyor mu? Bu,
alintinin UYDURULMADIGINI garanti eder ama alintinin DESTEKLEDIGI IDDIANIN
dogru olup olmadigini KONTROL ETMEZ.

Ornek (ChatGPT review'inde isaret edildi): kaynak "Basvuru 7 is gunu
icinde DEGERLENDIRILIR" diyor, model govdede "Basvurunun KESIN OLARAK
KABUL EDILMESI 7 is gunu icinde TAMAMLANIR" yazip ayni (dogru, birebir)
alintiyi gosterebilir. citation_guard bunu "sorun yok" der (alinti
kaynakta var), ama IDDIA kaynaktan daha GUCLU/FARKLI bir sey soyluyor
(degerlendirme != kabul). Bu modul, cevabin GOVDESINDEKI her iddiayi
(claim) ayiklayip, atifta bulundugu kaynak(lar)in GERCEKTEN o iddiayi
destekleyip desteklemedigini (entailment) AYRI bir LLM cagrisiyla
kontrol eder - citation_guard'daki deterministik kontrolun bir ustu,
applicability_checker'in ("dogru hukum ailesi mi") tamamlayicisi
("dogru hukum, dogru GUCTE mi aktarilmis") olarak dusunulebilir.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..common.llm_router import LLMError, chat_completion_json

CLAIM_VERIFICATION_SYSTEM_PROMPT = """Sen bir hukuki iddia-dogrulama denetcisisin. Sana bir CEVAP METNI ve numarali KAYNAK PASAJLAR verilecek.

Gorevin: cevap metnindeki HER ayri iddiayi (claim - genelde bir cumle ya da madde isareti) ayikla. Her iddia icin:
1. O iddianin hangi kaynak numarasina/numaralarina dayandigini belirle (cevaptaki [N] isaretlerinden).
2. O kaynagin/kaynaklarin GERCEKTEN bu iddiayi destekleyip desteklemedigini degerlendir. ALINTININ KELIMESI KELIMESINE DOGRU OLMASI YETERLI DEGIL - iddia kaynaktan daha GUCLU, daha KESIN, farkli bir KAPSAMDA ya da FARKLI bir anlamda sunuluyorsa "desteklenmiyor" (supported: false) olarak isaretle.

Ozellikle su kaliplara dikkat et:
- Kaynak bir SURECI anlatirken ("degerlendirilir", "incelenir", "basvurulur"), iddia bir SONUCU kesinlestiriyorsa ("kabul edilir", "onaylanir", "tamamlanir") - bu bir carpitmadir.
- Kaynak DAR bir kosulu/ozneyi anlatirken ("X durumunda Y tesisleri icin"), iddia bunu GENISLETIYORSA ("tum Y'ler icin", kosulu dusurerek) - bu bir asiri-genellemedir.
- Kaynakta olmayan bir sayi/sure/taraf iddiaya EKLENMISSE.

Iddia, kaynagiyla TUTARLI/ESDEGER ya da kaynaktan daha DAR/temkinli bir ifadeyse "supported: true" ver. Sadece ACIKCA carpitma/asiri-genelleme/ekleme oldugunda false ver - belirsiz durumlarda true'ya egilimli ol (bu kontrol bir guvenlik agi, asiri hassas olup gereksiz yere alarm vermemeli).

Cevaptaki "Kaynak Alıntıları:" bolumunu (varsa) YOK SAY, sadece govde metnindeki iddialari degerlendir.

Sadece su JSON formatinda cevap ver, baska hicbir sey yazma:
{"claims": [{"text": "iddia metninin kisa bir ozeti", "citation_refs": [1, 2], "supported": true, "reason": "kisa (1 cumle) gerekce"}]}"""


@dataclass
class ClaimCheck:
    text: str
    citation_refs: list[int]
    supported: bool
    reason: str


@dataclass
class ClaimVerificationResult:
    claims: list[ClaimCheck] = field(default_factory=list)
    checked: bool = False  # LLM cagrisi basarili oldu mu

    @property
    def unsupported_claims(self) -> list[ClaimCheck]:
        return [c for c in self.claims if not c.supported]

    @property
    def has_unsupported_claims(self) -> bool:
        return bool(self.unsupported_claims)


def _format_sources(chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(f"[{i}] {c.get('text', '')}")
    return "\n\n".join(parts)


def _parse_citation_refs(raw: object) -> list[int]:
    if not isinstance(raw, list):
        return []
    refs = []
    for n in raw:
        try:
            refs.append(int(n))
        except (TypeError, ValueError):
            continue
    return refs


def verify_claims(answer_text: str, chunks: list[dict]) -> ClaimVerificationResult:
    """
    Kaynak yoksa ya da cevap govdesi bossa (orn. "bulamadim" tarzi bir
    cevap) kontrol ANLAMSIZDIR - checked=False, claims=[] doner (ne
    destekli ne desteksiz, çünkü değerlendirilecek bir iddia yok).

    LLM basarisiz olursa (kota/hata) AYNI sekilde checked=False doner -
    applicability_checker'da duzeltilen fail-open hatasini burada en
    bastan yapmiyoruz: "kontrol edilemedi" ile "kontrol edildi, sorun
    yok" ayni sey DEGILDIR (bkz. web/app.py'deki kullanim).
    """
    body = answer_text.split("Kaynak Alıntıları:")[0].strip()
    if not body or not chunks:
        return ClaimVerificationResult(claims=[], checked=False)

    user_prompt = f"CEVAP METNI:\n{body}\n\nKAYNAK PASAJLAR:\n{_format_sources(chunks)}"
    try:
        result = chat_completion_json(CLAIM_VERIFICATION_SYSTEM_PROMPT, user_prompt, temperature=0.0)
        raw_claims = result.get("claims", [])
        claims = [
            ClaimCheck(
                text=str(c.get("text", "")),
                citation_refs=_parse_citation_refs(c.get("citation_refs")),
                supported=bool(c.get("supported", True)),
                reason=str(c.get("reason", "") or ""),
            )
            for c in raw_claims
            if isinstance(c, dict)
        ]
        return ClaimVerificationResult(claims=claims, checked=True)
    except LLMError:
        return ClaimVerificationResult(claims=[], checked=False)
