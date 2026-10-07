import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.retrieval.question_bank import QUICK_QUESTIONS, QuestionBank, load_questions


def _write_eval(tmp_path, questions):
    p = tmp_path / "eval_set.json"
    p.write_text(json.dumps({"questions": questions}), encoding="utf-8")
    return p


def test_load_questions_keeps_positive_short_questions_and_quick_chips(tmp_path):
    p = _write_eval(tmp_path, [
        {"question": "Kanunun amaci nedir?", "expected_documents": ["kanun-6446"]},
        {"question": "Negatif test sorusu?", "expected_documents": []},
    ])
    qs = load_questions(p)
    assert "Kanunun amaci nedir?" in qs
    assert "Negatif test sorusu?" not in qs
    assert all(q in qs for q in QUICK_QUESTIONS)


def test_load_questions_drops_exam_command_phrasing_and_long_questions(tmp_path):
    p = _write_eval(tmp_path, [
        {"question": "'Bir abone ...' ifadesini değerlendirin.", "expected_documents": ["x"]},
        {"question": "Sorusuna mevzuata uygun cevap verin.", "expected_documents": ["x"]},
        {"question": "a" * 200, "expected_documents": ["x"]},
    ])
    qs = load_questions(p)
    assert qs == QUICK_QUESTIONS


def test_load_questions_dedupes_accent_variants(tmp_path):
    # Hizli soru ASCII, eval sorusu aksanli - ayni soru iki kez cikmamali.
    accented = "Kesinti süresi aştığında kullanıcılara ödenecek tazminat nasıl hesaplanır?"
    p = _write_eval(tmp_path, [{"question": accented, "expected_documents": ["x"]}])
    qs = load_questions(p)
    assert accented not in qs
    assert sum("esinti" in q for q in qs) == 1


def test_suggest_returns_closest_distinct_questions_excluding_near_duplicate():
    bank = QuestionBank(
        ["q-near-dup", "q-close", "q-close-copy", "q-far"],
        [[1.0, 0.0], [0.8, 0.6], [0.8, 0.6], [0.0, 1.0]],
    )
    # Sorgu vektoru q-near-dup ile ozdes -> o onerilmez; q-close ve kopyasi
    # ayni vektor oldugu icin sadece biri secilir; sonra q-far gelir.
    result = bank.suggest([1.0, 0.0], k=3)
    assert "q-near-dup" not in result
    assert result[-1] == "q-far"
    assert len([q for q in result if q.startswith("q-close")]) == 1


def test_suggest_respects_k():
    bank = QuestionBank(["a", "b", "c"], [[0.9, 0.436], [0.6, 0.8], [0.0, 1.0]])
    assert len(bank.suggest([1.0, 0.0], k=2)) == 2
