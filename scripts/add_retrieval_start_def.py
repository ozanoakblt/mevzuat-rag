from pathlib import Path
p = Path("scripts/run_eval.py")
s = p.read_text(encoding="utf-8")

old_body = """def run_single_question(
    question: dict, embedder, vector_store, bm25_index, reranker, with_generation: bool
) -> dict:
    q_text = question["question"]
    sub_queries = expand_query(q_text, embedder=embedder)"""
new_body = """def run_single_question(
    question: dict, embedder, vector_store, bm25_index, reranker, with_generation: bool
) -> dict:
    retrieval_start = time.perf_counter()
    q_text = question["question"]
    sub_queries = expand_query(q_text, embedder=embedder)"""

assert old_body in s, "fonksiyon basi bulunamadi - dosyanin guncel halini gonder"
s = s.replace(old_body, new_body)
p.write_text(s, encoding="utf-8")
print("Tamamlandi: retrieval_start tanimi eklendi.")
