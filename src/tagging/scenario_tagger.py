"""
Brief madde 9: "Groq ile kapalı uçlu sınıflandırma (bu metni oku, listeden
uygun 1-3 etiket seç) — serbest metin ürettirme, halüsinasyon riskini düşürür."

Bu modül her MADDE için (chunk için değil — brief madde 9: "dokümanlar...
aynı sabit listeden etiketlenir", madde seviyesi yeterli bağlam sağlar)
Groq'a kapalı-uçlu bir sınıflandırma sorusu sorar, yanıtı sabit listeye
karşı doğrular (listede olmayan bir etiket dönerse ATILIR — halüsinasyon
guard'ı).
"""
from __future__ import annotations

import logging

from ..common.groq_client import GroqError, chat_completion_json
from .scenario_taxonomy import TAXONOMY_PROMPT_LIST, VALID_TAGS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = f"""Sen bir Türk elektrik dağıtım mevzuatı sınıflandırma asistanısın.
Sana bir mevzuat maddesi metni verilecek. Görevin, bu maddenin AŞAĞIDAKİ SABİT
LİSTEDEN hangi senaryo kategorileriyle ilgili olduğunu belirlemek.

Sabit kategori listesi:
{TAXONOMY_PROMPT_LIST}

Kurallar:
- SADECE yukarıdaki listede olan id'leri kullan. Listede olmayan bir kategori UYDURMA.
- Madde bu kategorilerin HİÇBİRİYLE ilgili değilse boş liste döndür.
- En fazla 3 kategori seç, en fazla en alakalı olanları.
- Yanıtını SADECE şu JSON formatında ver, başka hiçbir metin ekleme:
{{"tags": ["id1", "id2"]}}
"""


def classify_madde_text(text: str, madde_baslik: str | None = None) -> list[str]:
    """
    Bir maddenin tam metnini sınıflandırır. Groq'a ulaşılamazsa veya yanıt
    geçersizse boş liste döner (hata durumunda sessizce yanlış etiket
    UYDURMAZ — brief madde 13: "kaynak bulunmuyorsa tahmin yapma" ilkesi
    etiketleme için de geçerli).
    """
    if not text.strip():
        return []

    user_prompt = f"Madde başlığı: {madde_baslik or '(başlık yok)'}\n\nMadde metni:\n{text[:3000]}"

    try:
        result = chat_completion_json(SYSTEM_PROMPT, user_prompt)
    except GroqError as exc:
        logger.warning("Groq sınıflandırma başarısız, etiket atanmadı: %s", exc)
        return []

    raw_tags = result.get("tags", [])
    if not isinstance(raw_tags, list):
        logger.warning("Groq yanıtı beklenmeyen formatta: %r", result)
        return []

    valid = [t for t in raw_tags if t in VALID_TAGS]
    invalid = [t for t in raw_tags if t not in VALID_TAGS]
    if invalid:
        logger.warning("Sabit listede olmayan etiketler atıldı: %s", invalid)

    return valid[:3]
