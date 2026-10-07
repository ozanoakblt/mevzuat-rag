"""
"Bunu mu sormak istediniz?" onerileri icin soru bankasi.

Dusuk guvenli cevaplarda (sistem "bulamadim"/uyari verdiginde) kullaniciya
bilinen, iyi cevaplanan sorulardan en yakin 3 tanesi onerilir. Banka,
eval/eval_set.json'daki pozitif sorulardan ve arayuzdeki hizli sorulardan
olusur; embedding'ler baslangicta BIR KEZ hesaplanir, oneri aninda ekstra
LLM cagrisi yoktur (sadece zaten hesaplanan soru embedding'i ile dot-product).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

QUICK_QUESTIONS = [
    "Baglanti ve sistem kullanim anlasmasi nasil yapilir?",
    "OSB katilimcilarinin sisteme baglantisi hangi mevzuata tabidir?",
    "Kesinti suresi astiginda kullanicilara odenecek tazminat nasil hesaplanir?",
    "EV sarj hizmeti hangi lisans kapsaminda yurutulur?",
]

# "... ifadesini degerlendirin", "... verin" gibi sinav-komutu kaliplari
# kullaniciya oneri olarak anlamsiz durur; ayrica cok uzun sorular chip'e sigmaz.
_EXCLUDE_RE = re.compile(r"(değerlendirin|degerlendirin|\bverin\b|özetleyin|ozetleyin|açıklayın|aciklayin)", re.I)
_MAX_LEN = 140

NEAR_DUPLICATE = 0.97  # kullanicinin sorusunun neredeyse aynisi olani onerme
_FOLD = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def load_questions(eval_set_path: Path) -> list[str]:
    questions = list(QUICK_QUESTIONS)
    if eval_set_path.exists():
        data = json.loads(eval_set_path.read_text(encoding="utf-8"))
        for q in data.get("questions", []):
            text = q["question"].strip()
            if (
                q.get("expected_documents")
                and len(text) <= _MAX_LEN
                and not text.startswith(("'", '"'))
                and not _EXCLUDE_RE.search(text)
            ):
                questions.append(text)
    # Hizli sorular ASCII, eval sorulari aksanli - ayni soru iki kez
    # (aksan farkiyla) onerilmesin diye aksan/buyuk-kucuk harf katlanmis
    # anahtarla tekillestiriyoruz.
    seen: set[str] = set()
    unique = []
    for q in questions:
        key = q.translate(_FOLD).lower()
        if key not in seen:
            seen.add(key)
            unique.append(q)
    return unique


class QuestionBank:
    def __init__(self, questions: list[str], vectors: list[list[float]]):
        self.questions = questions
        self.vectors = vectors

    @classmethod
    def build(cls, embedder, eval_set_path: Path) -> "QuestionBank":
        questions = load_questions(eval_set_path)
        vectors = [embedder.embed_query(q) for q in questions]
        return cls(questions, vectors)

    def suggest(self, question_vector: list[float], k: int = 3) -> list[str]:
        """
        Embedding'ler normalize oldugu icin dot-product = cosine. Alakali/
        alakasiz ayiran mutlak bir esik KASITLI olarak yok: E5 benzerlikleri
        kisa sorularda sikisik (olculdu: alakasiz "pizza nasil yapilir" 0.83,
        alakali sorular 0.85-0.90 - ifade kalibi ["nasil yapilir"] baskin).
        Bu yuzden en yakin k FARKLI soru her zaman doner; alakasiz bir soruda
        bu, "sistemin cevaplayabildigi konulara" ornek olarak islev gorur.
        """
        scored = sorted(
            (
                (sum(a * b for a, b in zip(question_vector, v)), q, v)
                for q, v in zip(self.questions, self.vectors)
            ),
            reverse=True,
        )
        chosen: list[tuple[str, list[float]]] = []
        for sim, q, v in scored:
            if sim >= NEAR_DUPLICATE:
                continue  # kullanicinin sorusunun neredeyse aynisi
            if any(sum(a * b for a, b in zip(v, cv)) >= NEAR_DUPLICATE for _, cv in chosen):
                continue  # zaten secilmis bir onerinin (orn. aksan farkli) kopyasi
            chosen.append((q, v))
            if len(chosen) == k:
                break
        return [q for q, _ in chosen]
