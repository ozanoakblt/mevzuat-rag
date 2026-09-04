import pathlib

p = pathlib.Path("scripts/build_index.py")
text = p.read_text(encoding="utf-8")

anchor = '    logger.info("Tamamlandı. Toplam vektör sayısı: %d", store.count())'

addition = '''    logger.info("Tamamlandı. Toplam vektör sayısı: %d", store.count())

    # HNSW index'in arka planda tamamen diske yazilmasini (compaction)
    # bekleriz - bazi chromadb surumlerinde bu islem asenkron calisiyor ve
    # process hemen kapanirsa index dosyalari eksik/bozuk kalabiliyor.
    # Burada gercek bir sorgu calistirip sonra bekleyerek, index'in
    # process kapanmadan once diske yazilmasini garantiye almaya calisiyoruz.
    import time

    logger.info("Index'in diske tam yazilmasi icin dogrulama sorgusu calistiriliyor...")
    test_vec = embedder.embed_query("test sorgusu")
    for attempt in range(3):
        try:
            store.query(test_vec, n_results=1)
            logger.info("Dogrulama sorgusu basarili (deneme %d).", attempt + 1)
            break
        except Exception as exc:
            logger.warning("Dogrulama sorgusu basarisiz (deneme %d): %s", attempt + 1, exc)
            time.sleep(5)

    logger.info("Ek guvenlik bekleme suresi (10sn)...")
    time.sleep(10)
    logger.info("Bitti.")'''

if anchor not in text:
    print("HATA: anchor bulunamadi.")
else:
    new_text = text.replace(anchor, addition)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili.")
