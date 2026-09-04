import sys
sys.path.insert(0, ".")
from src.generation.citation_guard import detect_institution_conflation

test1 = "Bu, dağıtım şirketinin (TEİAŞ) SCADA sistemi üzerinden üretim tesisine set-point gönderebileceğini gösterir."
test2 = "Dağıtım şirketleri (TEİAŞ) set-point sinyalleri göndererek inverterlerin üretim çıkışını azaltabilir."
test3 = "Dağıtım şirketi bağlantı görüşünü 90 gün içinde bildirmelidir."

print("Test 1 (conflation var):", detect_institution_conflation(test1))
print("Test 2 (conflation var):", detect_institution_conflation(test2))
print("Test 3 (conflation yok):", detect_institution_conflation(test3))
