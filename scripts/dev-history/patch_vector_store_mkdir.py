import pathlib

p = pathlib.Path("src/embedding/vector_store.py")
text = p.read_text(encoding="utf-8")

old = "    def _save(self) -> None:\n        faiss.write_index(self._index, str(self._index_path))"
new = "    def _save(self) -> None:\n        self.persist_dir.mkdir(parents=True, exist_ok=True)\n        faiss.write_index(self._index, str(self._index_path))"

if old not in text:
    print("HATA: eslesme bulunamadi.")
else:
    new_text = text.replace(old, new)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili.")
