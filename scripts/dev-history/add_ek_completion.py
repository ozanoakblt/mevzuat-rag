import pathlib

p = pathlib.Path("web/app.py")
text = p.read_text(encoding="utf-8")

old = '''    top_chunks = _state["reranker"].rerank_with_safety_net(
        question, candidates, top_k=FINAL_TOP_K, guard_pool=guard_pool
    )
    try:
        answer = generate_answer(question, top_chunks, doc_titles=DOC_TITLES)'''

new = '''    top_chunks = _state["reranker"].rerank_with_safety_net(
        question, candidates, top_k=FINAL_TOP_K, guard_pool=guard_pool
    )

    # Eger secilen chunk'lardan biri bir "Ek" (EK) ise, ayni belgenin ayni
    # Ek numarasina sahip DIGER parcalarini da (candidates havuzundan)
    # otomatik ekle. Ekler (Ek-1..Ek-24) 4000 karakter siniriyla birden
    # fazla parcaya bolunuyor (bkz. metadata.py extract_appendices) ve
    # tek bir parca genelde konunun sadece bir kismini icerir - gercek bir
    # vakada tespit edildi: Ek-18'in E.18.3 parcasi TEIAS'tan bahsederken,
    # Madde 29 parcasi (ayri chunk) "dagitim sirketleri" ifadesini
    # iceriyordu ama ikisi ayni anda secilmeyebiliyordu.
    existing_ids = {c["chunk_id"] for c in top_chunks}
    ek_keys_selected = {
        (c["doc_id"], c["madde_no"])
        for c in top_chunks
        if c.get("madde_kind") == "EK"
    }
    if ek_keys_selected:
        extra_ek_chunks = [
            c
            for c in candidates
            if c.get("madde_kind") == "EK"
            and (c["doc_id"], c["madde_no"]) in ek_keys_selected
            and c["chunk_id"] not in existing_ids
        ]
        if extra_ek_chunks:
            top_chunks = top_chunks + extra_ek_chunks
            existing_ids.update(c["chunk_id"] for c in extra_ek_chunks)

    try:
        answer = generate_answer(question, top_chunks, doc_titles=DOC_TITLES)'''

count = text.count(old)
print("Kac yer eslesti:", count)

if count == 1:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("Basarili.")
else:
    print("HATA, elle kontrol gerekli.")
