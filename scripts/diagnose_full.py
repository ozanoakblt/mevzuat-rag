from pathlib import Path

src = Path("scripts/run_eval.py").read_text(encoding="utf-8")

full_old = """    parser = argparse.ArgumentParser()
    parser.add_argument("--with-generation", action="store_true")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="eval/results.json'daki tamamlanmis sorulari atlayip devam et",
    )
    args = parser.parse_args()

    eval_data = json.loads(EVAL_SET_PATH.read_text(encoding="utf-8"))
    questions = eval_data["questions"]

    chunks = load_all_chunks(PROCESSED_DIR)
    if not chunks:
        print("data/processed/ içinde chunk bulunamadı. Önce scripts/parse.py çalıştırın.")
        sys.exit(1)

    print(f"{len(questions)} soru yükleniyor, bileşenler hazırlanıyor...")
    embedder = Embedder()
    vector_store = VectorStore(persist_dir=VECTOR_STORE_DIR)
    bm25_index = BM25Index(chunks)
    reranker = Reranker()

    if vector_store.count() == 0:
        print("Vektör index boş. Önce python scripts/build_index.py çalıştırın.")
        sys.exit(1)

    results = []
    completed_ids: set[str] = set()
    RESULTS_PATH.parent.mkdir(exist_ok=True)
    if args.resume and RESULTS_PATH.exists():
        prev = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
        prev_results = prev.get("results", [])
        completed_ids = {
            r["id"] for r in prev_results
            if (not args.with_generation) or ("total_citation_count" in r)
        }
        # Sadece gercekten tamamlanmis kayitlari tut - ayni id icin eski
        # (farkli moddan kalma) kaydi listede birakip cift satir olusturma.
        results = [r for r in prev_results if r["id"] in completed_ids]
        print(f"Resume: {len(completed_ids)}/{len(questions)} soru daha once tamamlanmis, atlaniyor.")

    remaining = [q for q in questions if q["id"] not in completed_ids]"""

print("TAM BLOK ESLESIYOR MU:", full_old in src)

if full_old not in src:
    # Ilk farkli karakteri bul
    import difflib
    idx = src.find("    parser = argparse.ArgumentParser()")
    actual = src[idx:idx+len(full_old)+50]
    for i, (a, b) in enumerate(zip(full_old, actual)):
        if a != b:
            print(f"Ilk fark, pozisyon {i}:")
            print("  beklenen:", repr(full_old[max(0,i-20):i+20]))
            print("  gercek  :", repr(actual[max(0,i-20):i+20]))
            break
    else:
        print("Uzunluk farkli. beklenen uzunluk:", len(full_old), "gercek (kesilmis) uzunluk karsilastirmasi icin actual[:len(full_old)] kullanildi.")
