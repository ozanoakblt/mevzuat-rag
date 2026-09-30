import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.parsing.structure_parser import _turkish_upper, parse_document

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


# Kanun metinleri (orn. temel Elektrik Piyasasi Kanunu) genelde "Madde N -"
# (karisik harf) kullanir, Yonetmelik/Usul belgelerinin "MADDE N -" (tam
# buyuk) kalibinin aksine - gercek bir vakada bu, MADDE_RE'nin hicbir
# maddeyi yakalamamasina ve belgenin sessizce 0 chunk uretmesine yol acti.
MIXED_CASE_KANUN_TEXT = """Birinci Bölüm
Genel Hükümler
Madde 1 – (1) Bu Kanunun amacı test etmektir.
Madde 2 – (1) Bu Kanun test kapsamını düzenler.
İkinci Bölüm
Diğer Hükümler
Geçici Madde 1 – (1) Geçici hüküm metni.
"""


def test_mixed_case_madde_detected_like_kanun_documents():
    blocks = parse_document(MIXED_CASE_KANUN_TEXT)
    assert len(blocks) == 3
    assert blocks[0].madde_kind == "MADDE"
    assert blocks[0].madde_no == "1"
    assert blocks[0].bolum == "Genel Hükümler"


def test_mixed_case_gecici_madde_normalized_to_uppercase_kind():
    blocks = parse_document(MIXED_CASE_KANUN_TEXT)
    gecici = blocks[2]
    # kind_prefix kucuk harfle eslesse bile ("Geçici"), kanonik cikti
    # her zaman buyuk harfli "GEÇİCİ MADDE" olmali - diger tum kod
    # (run_eval.py, citation_guard.py vb.) bu formati bekliyor.
    assert gecici.madde_kind == "GEÇİCİ MADDE"
    assert gecici.madde_no == "1"


# AB Network Code cevirisi tarzi belgeler (orn. TEIAS'in "iletim sistemi
# isletimine iliskin kilavuz" serisi) "Madde N"yi satirin TAMAMI olarak
# yazar - tire yok, baslik bir sonraki satirda. Gercek bir vakada bu,
# 13 belgenin (~1.3M karakter) sessizce 0 chunk uretmesine yol acti.
NO_DASH_EU_STYLE_TEXT = """Madde 1
Konu
İşletme güvenliğini korumak amacıyla bu Tüzük aşağıdakiler hakkında ilkeler ortaya koymaktadır:
(a) işletme güvenliğine ilişkin gereksinimler;
(b) koordinasyon ve veri alışverişine ilişkin kurallar.
Madde 2
Kapsam
Bu Yönetmelikte belirtilen kurallar aşağıdaki SGU'lar için geçerli olacaktır.
"""


def test_no_dash_madde_header_detected_like_eu_style_documents():
    blocks = parse_document(NO_DASH_EU_STYLE_TEXT)
    assert len(blocks) == 2
    assert blocks[0].madde_kind == "MADDE"
    assert blocks[0].madde_no == "1"
    assert "İşletme güvenliğini korumak" in blocks[0].raw_text
    assert blocks[1].madde_no == "2"


def test_inline_madde_reference_does_not_create_false_boundary():
    # "Madde 5" satirin TAMAMI degilse (cumle icinde/sonrasinda baska
    # metin varsa), yanlislikla yeni bir madde siniri sayilmamali.
    text = "Madde 1\nKonu\nBu Kanunun Madde 5 hükmü uyarınca değerlendirilir.\nMadde 2\nKapsam\nmetin.\n"
    blocks = parse_document(text)
    assert len(blocks) == 2
    assert blocks[0].madde_no == "1"
    assert blocks[1].madde_no == "2"
    assert "Madde 5 hükmü uyarınca" in blocks[0].raw_text


def test_turkish_upper_handles_dotted_i_correctly():
    # Python'un duz .upper()'i "geçici" -> "GEÇICI" (yanlis, noktasiz I)
    # uretir; Turkce kurallarina gore dogrusu "GEÇİCİ" (noktali İ).
    assert _turkish_upper("geçici") == "GEÇİCİ"
    assert _turkish_upper("ek") == "EK"
    assert _turkish_upper("ısı") == "ISI"
