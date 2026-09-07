import pathlib

p = pathlib.Path("scripts/run_eval.py")
text = p.read_text(encoding="utf-8")

old = """    results = []
    for i, q in enumerate(questions, 1):
        print(f"  [{i}/{len(questions)}] {q['id']}: {q['question'][:60]}...")
        results.append(
            run_single_question(q, embedder, vector_store, bm25_index, reranker, args.with_generation)
        )"""

new = """    results = []
    RESULTS_PATH.parent.mkdir(exist_ok=True)
    for i, q in enumerate(questions, 1):
        print(f"  [{i}/{len(questions)}] {q['id']}: {q['question'][:60]}...")
        results.append(
            run_single_question(q, embedder, vector_store, bm25_index, reranker, args.with_generation)
        )
        # Checkpoint: her soru sonrasi ara sonucu diske yaz - uzun
        # calisan (--with-generation) modda rate-limit gibi bir kesinti
        # olursa, o ana kadarki sonuclar kaybolmasin (gercek bir vakada
        # 49 sorudan 24'u basariyla tamamlanmisken Groq 429 hatasi
        # verdi ve tum 24 sonuc bellekte kalip diske hic yazilamadi).
        partial_summary = summarize(results)
        RESULTS_PATH.write_text(
            json.dumps(
                {"summary": partial_summary, "results": results, "completed": i, "total": len(questions)},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )"""

count = text.count(old)
print("Kac yer eslesti:", count)
if count == 1:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("Basarili.")
else:
    print("HATA, elle kontrol gerekli.")
