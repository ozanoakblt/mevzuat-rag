import pathlib
import re

# 1) Iki test dosyasindaki mojibake'i (double-encoding) temizle
for f in ["tests/test_citation_guard.py", "tests/test_web_app.py"]:
    p = pathlib.Path(f)
    raw = p.read_text(encoding="utf-8-sig")
    try:
        fixed = raw.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        fixed = raw
    p.write_text(fixed, encoding="utf-8")
print("Encoding duzeltildi.")

# 2) test_citation_guard.py: assertion metinlerini ASCII uyari metnine gore guncelle
p = pathlib.Path("tests/test_citation_guard.py")
content = p.read_text(encoding="utf-8")
content = content.replace('"DÜŞÜK GÜVEN"', '"DUSUK GUVEN"')
content = content.replace('"DOĞRULANAMAYAN ALINTI"', '"DOGRULANAMAYAN ALINTI"')
p.write_text(content, encoding="utf-8")
print("test_citation_guard.py guncellendi.")

# 3) test_web_app.py: fake_chunk'a rrf_score ekle, FakeReranker imzasini guncelle,
#    expand_query'yi mockla (regex ile, tam metin esleslesmesine bagimli olmadan)
p = pathlib.Path("tests/test_web_app.py")
content = p.read_text(encoding="utf-8")

content = re.sub(
    r'("rerank_score":\s*3\.5,)',
    r'\1\n        "rrf_score": 0.05,',
    content,
)

content = content.replace(
    "def rerank_with_safety_net(self, query, candidates, top_k=5):",
    "def rerank_with_safety_net(self, query, candidates, top_k=5, guard_pool=None):",
)

content, n = re.subn(
    r'\n(\s*)\):\n(\s*result = web_app\.ask)',
    r'\n\1), patch.object(web_app, "expand_query", return_value=["test sorusu"]):\n\2',
    content,
)
print("expand_query patch eklendi mi:", n == 1)

p.write_text(content, encoding="utf-8")
print("test_web_app.py guncellendi.")
