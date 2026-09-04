import pathlib
import re

p = pathlib.Path("src/retrieval/reranker.py")
raw = p.read_text(encoding="utf-8-sig")
try:
    raw = raw.encode("cp1252").decode("utf-8")
except (UnicodeEncodeError, UnicodeDecodeError):
    pass

marker = "        reranked = self.rerank(query, candidates, top_k=top_k)"
idx = raw.index(marker)
head = raw[:idx]

tail = '''        reranked = self.rerank(query, candidates, top_k=top_k)
        if not candidates:
            return reranked

        guard_pool = guard_pool if guard_pool is not None else candidates[:guard_top_n]
        reranked_ids = {r["chunk_id"] for r in reranked}
        missing = [c for c in guard_pool if c["chunk_id"] not in reranked_ids]
        if not missing or not reranked:
            return reranked

        # Oncelik-tabanli kurtarma: guard_pool sirasi = onem sirasi (once
        # eklenen = daha onemli). Her "missing" oge, mevcut reranked
        # listesindeki EN DUSUK oncelikli (guard_pool'da yok = sonsuz
        # dusuk, ya da guard_pool'da daha gec siradaki) slotu, KENDI
        # onceliginden daha kotu ise ezer. Boylece yuksek oncelikli bir
        # sonuc (or. hybrid'in 1 numarasi), guard havuzu buyuk oldugunda
        # bile asla dusuk oncelikli baska bir guard uyesi tarafindan
        # yanlislikla silinmez (gercek vakada tespit edilen hata buydu).
        priority = {c["chunk_id"]: i for i, c in enumerate(guard_pool)}
        base_score = min(r["rerank_score"] for r in reranked)

        for i, rescue in enumerate(missing):
            rescue_priority = priority[rescue["chunk_id"]]
            worst_idx = None
            worst_priority = -1
            for idx2, r in enumerate(reranked):
                p2 = priority.get(r["chunk_id"], float("inf"))
                if worst_idx is None or p2 > worst_priority or (
                    p2 == worst_priority
                    and r["rerank_score"] < reranked[worst_idx]["rerank_score"]
                ):
                    worst_idx = idx2
                    worst_priority = p2
            if worst_idx is None or worst_priority <= rescue_priority:
                continue
            reranked[worst_idx] = {
                **rescue,
                "rerank_score": base_score - (i + 1) * 1e-6,
                "rescued_by_safety_net": True,
            }

        reranked.sort(key=lambda c: c["rerank_score"], reverse=True)
        return reranked
'''

new_raw = head + tail
p.write_text(new_raw, encoding="utf-8")
print("Yeni uzunluk:", len(new_raw))
