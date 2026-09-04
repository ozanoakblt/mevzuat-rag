import pathlib

p = pathlib.Path("web/static/app.js")
text = p.read_text(encoding="utf-8")

old = '''function renderAnswerBody(rawText) {
  const splitIdx = rawText.search(/Kaynak Alıntıları:?/i);
  const mainText = splitIdx >= 0 ? rawText.slice(0, splitIdx).trim() : rawText.trim();

  const paragraphs = mainText'''

new = '''function renderAnswerBody(rawText) {
  const splitIdx = rawText.search(/Kaynak Alıntıları:?/i);
  let mainText = splitIdx >= 0 ? rawText.slice(0, splitIdx).trim() : rawText.trim();

  // Model bazen "Kaynak Alıntıları:" basligindan hemen once bos bir
  // ayirici satir birakiyor (orn. sadece "**" ya da "---" / "###" iceren
  // bir paragraf). Bu, kesme noktasinin ONCESINDE kaldigi icin mainText'in
  // sonunda kalip bos bir kalin yazi/baslik olarak gorunuyordu - burada
  // sondan baslayarak sadece markdown isaretlerinden olusan satirlari
  // temizliyoruz.
  const lines = mainText.split(/\\n+/);
  while (lines.length && /^[\\s#*\\-_]*$/.test(lines[lines.length - 1])) {
    lines.pop();
  }
  mainText = lines.join("\\n").trim();

  const paragraphs = mainText'''

if old not in text:
    print("HATA: eslesme bulunamadi.")
else:
    new_text = text.replace(old, new)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili.")
