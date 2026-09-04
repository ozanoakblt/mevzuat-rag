import pathlib

p = pathlib.Path("scripts/build_index.py")
text = p.read_text(encoding="utf-8")

old = """    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["embedding_text"] for c in batch]
        embeddings = embedder.embed_passages(texts)
        store.upsert_chunks(batch, embeddings)
        logger.info("  %d/%d chunk işlendi", min(i + BATCH_SIZE, len(chunks)), len(chunks))

    logger.info("Tamamlandı. Toplam vektör sayısı: %d", store.count())"""

new = """    all_embeddings = []
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["embedding_text"] for c in batch]
        embeddings = embedder.embed_passages(texts)
        all_embeddings.extend(embeddings)
        logger.info("  %d/%d embedding hesaplandi", min(i + BATCH_SIZE, len(chunks)), len(chunks))

    logger.info("Tum embedding'ler hesaplandi, Chroma'ya TEK seferde yaziliyor...")
    store.upsert_chunks(chunks, all_embeddings)
    logger.info("Tamamlandı. Toplam vektör sayısı: %d", store.count())"""

if old not in text:
    print("HATA: eslesme bulunamadi.")
else:
    new_text = text.replace(old, new)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili.")
