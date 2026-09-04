import sys
sys.path.insert(0, ".")
from src.generation.citation_guard import detect_institution_conflation

test1 = "dağıtım şirketlerinin (örneğin TEİAŞ) inverterlara set point göndermesi"
test2 = "dağıtım şirketinin (TEİAŞ) SCADA sistemi"
test3 = "dağıtım şirketi bağlantı görüşünü 90 gün içinde bildirmelidir"

print("Test 1 (orneğin ile, yakalanmali):", detect_institution_conflation(test1))
print("Test 2 (eski format, yakalanmali):", detect_institution_conflation(test2))
print("Test 3 (normal, yakalanmamali):", detect_institution_conflation(test3))
