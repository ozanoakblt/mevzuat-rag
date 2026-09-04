import pathlib

p = pathlib.Path("web/static/app.js")
text = p.read_text(encoding="utf-8")

# --- A) cite span'lara data-cite ekle ---
old_a = '''html = html.replace(/\\[(\\d+)\\]/g, \'<span class="cite">$1</span>\');'''
new_a = '''html = html.replace(/\\[(\\d+)\\]/g, \'<span class="cite" data-cite="$1">$1</span>\');'''
if old_a not in text:
    print("HATA A: cite regex bulunamadi.")
else:
    text = text.replace(old_a, new_a, 1)

# --- B) global currentBlockEl degiskeni ekle (dosya basina) ---
old_b = "const stageEl = document.querySelector(\\".stage\\");"
new_b = "let currentBlockEl = null;\\nconst stageEl = document.querySelector(\\".stage\\");"
if old_b not in text:
    print("HATA B: stageEl satiri bulunamadi.")
else:
    text = text.replace(old_b, new_b, 1)

# --- C) resetSourcePanel / renderSourcePanel fonksiyonlarini genislet ---
old_c = """function resetSourcePanel() {
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

new_c = """function resetSourcePanel() {
  const body = document.getElementById("sourcePanelBody");
  const countEl = document.getElementById("sourcePanelCount");
  const led = document.getElementById("sourcePanelLed");
  countEl.textContent = "";
  led.hidden = true;
  currentBlockEl = null;
  body.innerHTML = `<div class="source-panel-empty" id="sourcePanelEmpty">Bir soru sordugunuzda, cevabin dayandigi madde ve fikralar burada listelenir.</div>`;
}

function showSourcePanelSkeleton() {
  const body = document.getElementById("sourcePanelBody");
  const countEl = document.getElementById("sourcePanelCount");
  const led = document.getElementById("sourcePanelLed");
  countEl.textContent = "";
  led.hidden = true;
  const card = `
    <div class="source-skeleton-card">
      <div class="skeleton-line w-40"></div>
      <div class="skeleton-line w-70"></div>
      <div class="skeleton-line w-90"></div>
      <div class="skeleton-line w-60"></div>
    </div>`;
  body.innerHTML = card.repeat(3);
}

function renderSourcePanel(sources, blockEl, isLow) {
  currentBlockEl = blockEl || null;
  const body = document.getElementById("sourcePanelBody");
  const countEl = document.getElementById("sourcePanelCount");
  const led = document.getElementById("sourcePanelLed");
  countEl.textContent = sources.length ? `${sources.length} kaynak` : "";
  led.hidden = sources.length === 0;
  led.classList.toggle("low", !!isLow);
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
        <div class="source-panel-card" data-idx="${i + 1}">
          <div class="card-head">
            <span class="idx-badge">${i + 1}</span>
            <span class="loc">${escapeHtml(loc)}</span>
          </div>
          <span class="doc-title">${escapeHtml(s.doc_title)}</span>
          <div class="body-text">${escapeHtml(s.text)}</div>
        </div>`;
    })
    .join("");
}

function highlightSourceCard(idx, temporary) {
  document.querySelectorAll(".source-panel-card.hover-highlight, .source-panel-card.active-highlight")
    .forEach((el) => el.classList.remove("hover-highlight", "active-highlight"));
  const card = document.querySelector(`.source-panel-card[data-idx="${idx}"]`);
  if (!card) return;
  card.classList.add(temporary ? "hover-highlight" : "active-highlight");
  if (!temporary) {
    card.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}"""

if old_c not in text:
    print("HATA C: resetSourcePanel/renderSourcePanel bulunamadi.")
else:
    text = text.replace(old_c, new_c, 1)

# --- D) qaScrollEl click handler icine cite tiklama davranisi ekle ---
old_d = """  const retryBtn = e.target.closest("[data-retry]");
  if (retryBtn) {
    askQuestion(retryBtn.dataset.retry);
  }
});"""

new_d = """  const retryBtn = e.target.closest("[data-retry]");
  if (retryBtn) {
    askQuestion(retryBtn.dataset.retry);
  }

  const citeBtn = e.target.closest(".cite");
  if (citeBtn) {
    const ownerBlock = citeBtn.closest(".qa-block");
    if (ownerBlock === currentBlockEl) {
      highlightSourceCard(citeBtn.dataset.cite, false);
    }
  }
});

qaScrollEl.addEventListener("mouseover", (e) => {
  const citeBtn = e.target.closest(".cite");
  if (!citeBtn) return;
  const ownerBlock = citeBtn.closest(".qa-block");
  if (ownerBlock === currentBlockEl) {
    highlightSourceCard(citeBtn.dataset.cite, true);
  }
});

qaScrollEl.addEventListener("mouseout", (e) => {
  const citeBtn = e.target.closest(".cite");
  if (!citeBtn) return;
  document.querySelectorAll(".source-panel-card.hover-highlight")
    .forEach((el) => el.classList.remove("hover-highlight"));
});"""

if old_d not in text:
    print("HATA D: retryBtn bloğu bulunamadi.")
else:
    text = text.replace(old_d, new_d, 1)

# --- E) askQuestion basinda iskelet goster ---
old_e = """  qaScrollEl.appendChild(block);
  inputEl.value = "";
  inputEl.style.height = "auto";
  submitEl.disabled = true;
  block.scrollIntoView({ behavior: "smooth", block: "start" });"""

new_e = """  qaScrollEl.appendChild(block);
  inputEl.value = "";
  inputEl.style.height = "auto";
  submitEl.disabled = true;
  block.scrollIntoView({ behavior: "smooth", block: "start" });
  showSourcePanelSkeleton();"""

if old_e not in text:
    print("HATA E: qaScrollEl.appendChild bloğu bulunamadi.")
else:
    text = text.replace(old_e, new_e, 1)

# --- F) renderAnswer cagrisinda block ve isLow ilet ---
old_f = "  renderSourcePanel(data.sources);"
new_f = "  renderSourcePanel(data.sources, block, isLow);"
if old_f not in text:
    print("HATA F: renderSourcePanel cagrisi bulunamadi.")
else:
    text = text.replace(old_f, new_f, 1)

pathlib.Path("web/static/app.js").write_text(text, encoding="utf-8")
print("app.js guncellendi.")
