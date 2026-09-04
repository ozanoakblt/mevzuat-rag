import pathlib

p = pathlib.Path("web/static/app.js")
lines = p.read_text(encoding="utf-8").split("\n")

# resetSourcePanel: satir 53-58 (0-index), renderSourcePanel: satir 60-84
old_block = "\n".join(lines[53:84])

expected_start = "function resetSourcePanel() {"
expected_end = "    .join(\"\");"
if expected_start not in lines[53] or expected_end not in lines[83]:
    print("HATA: satir araligi beklenenle eslesmiyor.")
    print("lines[53]:", lines[53])
    print("lines[83]:", lines[83])
else:
    new_block = """function resetSourcePanel() {
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
    new_lines = new_block.split("\n")
    lines = lines[:53] + new_lines + lines[84:]
    p.write_text("\n".join(lines), encoding="utf-8")
    print("Basarili, fonksiyonlar degistirildi.")
