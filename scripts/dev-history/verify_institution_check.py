text = open("src/generation/citation_guard.py", encoding="utf-8").read()
print("detect_institution_conflation tanimi:", "def detect_institution_conflation" in text)
print("run_guard icinde cagriliyor:", "has_conflation = detect_institution_conflation" in text)
