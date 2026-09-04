import pathlib
import re

p = pathlib.Path("src/retrieval/reranker.py")
raw = p.read_text(encoding="utf-8-sig")

# Once dosyanin geri kalanindaki encoding'i de duzelt (docstring dahil)
try:
    raw = raw.encode("cp1252").decode("utf-8")
except (UnicodeEncodeError, UnicodeDecodeError):
    pass

# Eski dongu blogunu (idx_to_replace = len(reranked)-1-i ... return reranked)
# baslangicindan ("for i, rescue in enumerate(missing):") sonuna (fonksiyon sonu)
# kadar regex ile bul ve guvenli versiyonla degistir.
pattern = re.compile(
    r"        for i, rescue in enumerate\(missing\):.*?\n        return reranked\n",
    re.DOTALL,
)

replacement = '''        # Guard havuzundaki ogeler zaten reranked icindeyse KORUNMALIDIR -
        # kurtarma dongusu onlarin yerine baska bir seyi asla yazmamali.
        # Aksi halde guard_pool ile top_k boyutu esitlendiginde (ya da missing
        # sayisi buyudugunde), dogru bulunmus en iyi sonuc bile zayif bir
        # "missing" ogesiyle ezilebiliyordu (gercek bir vaka ile tespit edildi:
        # hedef skor=5.54 ile 1. siradayken, missing listesi 8 oge oldugunda
        # index 0'a kadar geri sararak onu siliyordu).
        protected_ids = {c["chunk_id"] for c in guard_pool}
        base_score = min(r["rerank_score"] for r in reranked)
        replace_idx = len(reranked) - 1
        for i, rescue in enumerate(missing):
            while replace_idx >= 0 and reranked[replace_idx]["chunk_id"] in protected_ids:
                replace_idx -= 1
            if replace_idx < 0:
                break
            reranked[replace_idx] = {
                **rescue,
                "rerank_score": base_score - (i + 1) * 1e-6,
                "rescued_by_safety_net": True,
            }
            replace_idx -= 1

        reranked.sort(key=lambda c: c["rerank_score"], reverse=True)
        return reranked
'''

new_raw, n = pattern.subn(replacement, raw)
print("Kac yer degisti:", n)

p.write_text(new_raw, encoding="utf-8")
