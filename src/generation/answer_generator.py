"""
Faz 8: Retrieval'ın bulduğu pasajlara dayanarak Groq ile cevap üretme.

Sistem promptu brief madde 13'teki 8 kuralı doğrudan uygular:
  1. Context dışında bilgi üretme.
  2. Kaynak bulunmuyorsa tahmin yapma.
  3. Madde numarası veya kaynak URL'si uydurma.
  4. Mülga mevzuatı güncel gibi gösterme.
  5. Çelişkili kaynak varsa kullanıcıya açıkça bildir.
  6. Her cevapta kaynak göster.
  7. Hukuki yorum ile mevzuat metnini ayır; hukuki danışmanlık verme.
  8. Kullanıcıya gerektiğinde resmî metni kontrol etmesini öner.

Faz 9'da buna ek olarak: üretilen cevaptaki atıfların (citation) gerçekten
verilen context'te var olup olmadığını doğrulayan bir katman eklenecek
(halüsinasyon guard'ı) — bu modül üretimi yapar, Faz 9 onu denetler.
"""
from __future__ import annotations

from ..common.groq_client import chat_completion_text

SYSTEM_PROMPT = """Sen Türkiye elektrik dağıtım sektörü için bir mevzuat araştırma asistanısın.
Elektrik-elektronik mühendislerine EPDK mevzuatı (kanun, yönetmelik) hakkında
sorularını, SANA VERİLEN KAYNAK PASAJLARA dayanarak cevaplarsın.

KURALLAR (bunlara istisnasız uy):
1. SADECE sana verilen kaynak pasajlardaki bilgiyi kullan. Pasajlarda
   olmayan hiçbir bilgiyi ekleme, genel bilgi birikiminden tahmin yapma.
2. Verilen pasajlar soruyu cevaplamıyorsa veya yetersizse, bunu AÇIKÇA
   belirt ("Verilen kaynaklarda bu konuda yeterli bilgi bulamadım" gibi).
   Zorla bir cevap uydurma.
3. Madde numarası, fıkra numarası veya herhangi bir referansı ASLA uydurma
   — sadece sana verilen pasajların üstünde yazan madde/fıkra/bent
   bilgisini kullan.
4. Bir pasaj mülga (yürürlükten kaldırılmış) ya da değişikliğe uğramış
   görünüyorsa, bunu güncelmiş gibi sunma; belirsizlik varsa söyle.
5. Farklı pasajlar birbiriyle çelişiyor gibi görünüyorsa, bunu kullanıcıya
   açıkça bildir, çelişkiyi kendi başına "çöz"meye çalışma.
6. ÖZETLERKEN KAPSAMI DARALTMA: kaynak metinde "ve", "veya", "ancak",
   "hariç" gibi bağlaçlar varsa, özetinde bunları SESSİZCE düşürme. Örnek:
   kaynak "X Yönetmeliği VE Y Yönetmeliği'ne göre incelenir" diyorsa,
   cevabın "sadece Y Yönetmeliği'ne tabidir" gibi tek taraflı bir izlenim
   VERMEMELİ.
7. Cevabının HER iddiası için, hangi pasajdan geldiğini [1], [2] gibi
   numaralarla işaretle.
8. Cevabının SONUNA, kullandığın HER [N] referansı için kaynak pasajdan
   BİREBİR (kelimesi kelimesine, en fazla 20 kelimelik) bir alıntıyı şu
   formatta ekle — bu, iddialarının denetlenebilmesi içindir:
   Kaynak Alıntıları:
   [1]: "pasajdan birebir alınmış kısa alıntı"
   [2]: "pasajdan birebir alınmış kısa alıntı"
9. Hukuki yorum yapma, hukuki danışmanlık verme — sadece mevzuat metninin
   ne dediğini aktar. Yorum gerekiyorsa bunun senin yorumun olduğunu ve
   bağlayıcı olmadığını belirt.
10. Cevabının gövdesinde (Kaynak Alıntıları bölümü hariç), kullanıcıya
    kesinlik gerektiren durumlarda resmî metni kontrol etmesini hatırlat.

Cevabını Türkçe, net ve öz yaz."""


def _format_context(chunks: list[dict], doc_titles: dict[str, str] | None = None) -> str:
    doc_titles = doc_titles or {}
    parts = []
    for i, c in enumerate(chunks, 1):
        title = doc_titles.get(c["doc_id"], c["doc_id"])
        loc = f"Madde {c.get('madde_no')}"
        if c.get("fikra_no"):
            loc += f", fıkra ({c['fikra_no']})"
        if c.get("bent_no"):
            loc += f", bent {c['bent_no']})"
        header = f"[{i}] Kaynak: {title} — {loc}"
        if c.get("madde_baslik"):
            header += f" ({c['madde_baslik']})"
        parts.append(f"{header}\n{c['text']}")
    return "\n\n".join(parts)


def generate_answer(
    query: str,
    chunks: list[dict],
    doc_titles: dict[str, str] | None = None,
    model: str | None = None,
) -> str:
    """
    chunks: retrieval pipeline'dan gelen (rerank edilmiş) sonuçlar, her biri
    en az "text", "doc_id", "madde_no" alanlarını içermeli.
    doc_titles: doc_id -> okunabilir başlık eşlemesi (ör. sources.py'deki
    SourceDoc.title). Verilmezse doc_id doğrudan kullanılır.
    """
    if not chunks:
        return (
            "Verilen kaynaklarda bu soruyla ilgili hiçbir pasaj bulunamadı. "
            "Lütfen sorunuzu farklı bir şekilde ifade etmeyi deneyin ya da "
            "resmî EPDK/mevzuat.gov.tr kaynaklarını doğrudan kontrol edin."
        )

    context = _format_context(chunks, doc_titles)
    user_prompt = f"KAYNAK PASAJLAR:\n\n{context}\n\nSORU: {query}"

    return chat_completion_text(SYSTEM_PROMPT, user_prompt, model=model)
