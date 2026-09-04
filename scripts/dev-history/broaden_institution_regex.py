import pathlib

p = pathlib.Path("src/generation/citation_guard.py")
text = p.read_text(encoding="utf-8")

old = '''_INSTITUTION_CONFLATION_RE = _re.compile(
    r"(dağıtım\\s+şirket\\w*|TEİAŞ|EPDK)\\s*\\((dağıtım\\s+şirket\\w*|TEİAŞ|EPDK)\\)",
    _re.IGNORECASE,
)'''

new = '''_INSTITUTION_CONFLATION_RE = _re.compile(
    r"(dağıtım\\s+şirket\\w*|TEİAŞ|EPDK)\\s*"
    r"\\((?:örneğin|ör\\.?|yani|diğer\\s+bir\\s+deyişle|misal)?\\s*"
    r"(dağıtım\\s+şirket\\w*|TEİAŞ|EPDK)\\)",
    _re.IGNORECASE,
)'''

count = text.count(old)
print("Kac yer eslesti:", count)

if count == 1:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("Basarili.")
else:
    print("HATA, elle kontrol gerekli.")
