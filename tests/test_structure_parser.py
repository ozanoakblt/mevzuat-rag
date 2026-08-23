import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.parsing.structure_parser import parse_document

SAMPLE_TEXT = """BİRİNCİ BÖLÜM
Amaç, Kapsam ve Tanımlar
Amaç
MADDE 1 – (1) Bu Kanunun amacı test etmektir.
Kapsam
MADDE 2 – (1) Bu Kanun test kapsamını düzenler.
Tanımlar ve kısaltmalar
MADDE 3 – (1) Bu Kanunun uygulanmasında;
a) Terim bir: birinci tanım,
b) Terim iki: ikinci tanım,
c) (Değişik:RG-1/1/2020-1) Terim üç: üçüncü tanım,
ifade eder.
İKİNCİ BÖLÜM
Diğer Hükümler
Yürürlük
GEÇİCİ MADDE 1 – (1) Geçici hüküm metni.
"""


def test_bolum_and_madde_detection():
    blocks = parse_document(SAMPLE_TEXT)
    assert len(blocks) == 4
    assert blocks[0].madde_no == "1"
    assert blocks[0].madde_baslik == "Amaç"
    assert blocks[0].bolum == "Amaç, Kapsam ve Tanımlar"


def test_title_not_leaked_into_previous_madde():
    blocks = parse_document(SAMPLE_TEXT)
    madde1 = blocks[0]
    assert "Kapsam" not in madde1.raw_text


def test_kapsam_title_assigned_to_madde2():
    blocks = parse_document(SAMPLE_TEXT)
    madde2 = blocks[1]
    assert madde2.madde_baslik == "Kapsam"


def test_tanimlar_bent_split():
    blocks = parse_document(SAMPLE_TEXT)
    madde3 = blocks[2]
    assert madde3.is_tanimlar
    fikra = madde3.fikralar[0]
    assert len(fikra.bents) == 3
    assert fikra.bents[0].bent_no == "a"
    assert fikra.bents[2].amendment_refs == ["(Değişik:RG-1/1/2020-1)"]


def test_gecici_madde_detected_in_new_bolum():
    blocks = parse_document(SAMPLE_TEXT)
    gecici = blocks[3]
    assert gecici.madde_kind == "GEÇİCİ MADDE"
    assert gecici.madde_no == "1"
    assert gecici.bolum == "Diğer Hükümler"
    assert gecici.madde_baslik == "Yürürlük"
