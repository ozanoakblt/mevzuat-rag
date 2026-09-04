import pathlib

p = pathlib.Path("web/static/app.js")
text = p.read_text(encoding="utf-8")

# 1) newChatBtn click: source panel'i de sifirla
old1 = """newChatBtn.addEventListener("click", () => {
  qaScrollEl.innerHTML = "";
  stageEl.classList.remove("chat-active");
  newChatBtn.hidden = true;
  inputEl.focus();
});"""

new1 = """newChatBtn.addEventListener("click", () => {
  qaScrollEl.innerHTML = "";
  stageEl.classList.remove("chat-active");
  newChatBtn.hidden = true;
  resetSourcePanel();
  inputEl.focus();
});

function resetSourcePanel() {
  const body = document.getElementById("sourcePanelBody");
  const countEl = document.getElementById("sourcePanelCount");
  countEl.textContent = "";
  body.innerHTML = `<div class="source-panel-empty" id="sourcePanelEmpty">Bir soru sordugunuzda, cevabin dayandigi madde ve fikralar burada listelenir.</div>`;
}

function renderSourcePanel(sources) {
  const body = document.getElementById("sourcePanelBody");
  const countEl = document.getElementById("sourcePanelCount");
  countEl.textContent = sources.length ? `${sources.length} kaynak` : "";
  if (!sources.length) {
    resetSourcePanel();
    return;
  }
  body.innerHTML = sources
    .map((s, i) => {
      const loc = ["Madde " + s.madde_no, s.fikra_no ? `fikra (${s.fikra_no})` : null, s.bent_no ? `bent ${s.bent_no})` : null]
        .filter(Boolean)
        .join(", ");
      return `
        <div class="source-panel-card">
          <div class="card-head">
            <span class="idx-badge">${i + 1}</span>
            <span class="loc">${escapeHtml(loc)}</span>
          </div>
          <span class="doc-title">${escapeHtml(s.doc_title)}</span>
          <div class="body-text">${escapeHtml(s.text)}</div>
        </div>`;
    })
    .join("");
}"""

if old1 not in text:
    print("HATA: newChatBtn bloğu bulunamadi.")
else:
    text = text.replace(old1, new1, 1)

# 2) renderAnswer icinde sag paneli de doldur
old2 = """function renderAnswer(block, question, data) {
  const isLow = data.confidence_level === "low";
  const bodyHtml = renderAnswerBody(data.answer);
  const rawForCopy = escapeAttr(data.answer);"""

new2 = """function renderAnswer(block, question, data) {
  const isLow = data.confidence_level === "low";
  const bodyHtml = renderAnswerBody(data.answer);
  const rawForCopy = escapeAttr(data.answer);
  renderSourcePanel(data.sources);"""

if old2 not in text:
    print("HATA: renderAnswer bloğu bulunamadi.")
else:
    text = text.replace(old2, new2, 1)

pathlib.Path("web/static/app.js").write_text(text, encoding="utf-8")
print("app.js guncellendi.")
