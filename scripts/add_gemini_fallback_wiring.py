from pathlib import Path

p1 = Path("src/generation/answer_generator.py")
s1 = p1.read_text(encoding="utf-8")
old1 = "from ..common.groq_client import chat_completion_text"
new1 = "from ..common.llm_router import chat_completion_text"
assert old1 in s1, "answer_generator.py import satiri bulunamadi"
s1 = s1.replace(old1, new1)
p1.write_text(s1, encoding="utf-8")

p2 = Path("src/retrieval/query_expansion.py")
s2 = p2.read_text(encoding="utf-8")
old2 = "from src.common.groq_client import GroqError, chat_completion_json"
new2 = "from src.common.llm_router import LLMError, chat_completion_json"
assert old2 in s2, "query_expansion.py import satiri bulunamadi"
s2 = s2.replace(old2, new2)
old3 = "    except GroqError:"
new3 = "    except LLMError:"
assert old3 in s2, "query_expansion.py except satiri bulunamadi"
s2 = s2.replace(old3, new3)
p2.write_text(s2, encoding="utf-8")

print("Tamamlandi: import lar llm_router a yonlendirildi.")
