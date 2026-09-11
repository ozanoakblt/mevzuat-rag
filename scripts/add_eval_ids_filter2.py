from pathlib import Path

PATH = Path("scripts/run_eval.py")
src = PATH.read_text(encoding="utf-8")

old = """    parser = argparse.ArgumentParser()
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

new = """    parser = argparse.ArgumentParser()
    parser.add_argument("--with-generation", action="store_true")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="eval/results.json'daki tamamlanmis sorulari atlayip devam et",
    )
    parser.add_argument(
        "--ids",
        type=str,
        default=None,
        help=(
            "virgulle ayrilmis soru id listesi (ornegin q02,q08,q49) - "
            "sadece bu sorulari, tamamlanmis olsalar bile ZORLA yeniden "
            "calistirir; results.json'daki diger tum kayitlari degistirmeden "
            "birakir. --resume ile birlikte kullanilirsa --ids kazanir."
        ),
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

    RESULTS_PATH.parent.mkdir(exist_ok=True)
    results = []
    completed_ids: set[str] = set()

    if args.ids:
        target_ids = {t.strip() for t in args.ids.split(",") if t.strip()}
        unknown = target_ids - {q["id"] for q in questions}
        if unknown:
            print(f"UYARI: eval_set.json'da olmayan id'ler: {sorted(unknown)}")
        if RESULTS_PATH.exists():
            prev = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
            results = [r for r in prev.get("results", []) if r["id"] not in target_ids]
        print(f"Hedefli calistirma: {len(target_ids)} soru ZORLA yeniden calisacak, digerleri korunuyor.")
        remaining = [q for q in questions if q["id"] in target_ids]
    elif args.resume and RESULTS_PATH.exists():
        prev = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
        prev_results = prev.get("results", [])
        completed_ids = {
            r["id"] for r in prev_results
            if (not args.with_generation) or ("total_citation_count" in r)
        }
        results = [r for r in prev_results if r["id"] in completed_ids]
        print(f"Resume: {len(completed_ids)}/{len(questions)} soru daha once tamamlanmis, atlaniyor.")
        remaining = [q for q in questions if q["id"] not in completed_ids]
    else:
        remaining = questions"""

assert old in src, "beklenen blok bulunamadi"
src = src.replace(old, new)
PATH.write_text(src, encoding="utf-8")
print("Tamamlandi: --ids eklendi.")
