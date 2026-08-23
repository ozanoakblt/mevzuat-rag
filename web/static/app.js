const stageEl = document.querySelector(".stage");
const qaScrollEl = document.getElementById("qaScroll");
const formEl = document.getElementById("askForm");
const inputEl = document.getElementById("questionInput");
const submitEl = document.getElementById("askSubmit");
const chipsEl = document.getElementById("quickChips");
const newChatBtn = document.getElementById("newChatBtn");
const conversationEl = document.getElementById("conversation");

const ICONS = {
  copy: `<svg viewBox="0 0 24 24" fill="none"><rect x="9" y="9" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.6"/><path d="M5 15V5a2 2 0 0 1 2-2h10" stroke="currentColor" stroke-width="1.6"/></svg>`,
  retry: `<svg viewBox="0 0 24 24" fill="none"><path d="M3 12a9 9 0 1 1 3 6.7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M3 21v-6h6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  up: `<svg viewBox="0 0 24 24" fill="none"><path d="M7 10v11H3V10h4Zm4 11h7.5a2 2 0 0 0 2-1.7l1.2-8a2 2 0 0 0-2-2.3H14V5a3 3 0 0 0-3-3l-2 7v12Z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg>`,
  down: `<svg viewBox="0 0 24 24" fill="none"><path d="M17 14V3h4v11h-4Zm-4-11H5.5a2 2 0 0 0-2 1.7l-1.2 8a2 2 0 0 0 2 2.3H10v4a3 3 0 0 0 3 3l2-7V3Z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg>`,
  chevron: `<svg viewBox="0 0 24 24" fill="none"><path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
};

// Textarea otomatik yükseklik
inputEl.addEventListener("input", () => {
  inputEl.style.height = "auto";
  inputEl.style.height = Math.min(inputEl.scrollHeight, 160) + "px";
});

inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    formEl.requestSubmit();
  }
});

chipsEl.addEventListener("click", (e) => {
  const btn = e.target.closest(".chip");
  if (!btn) return;
  inputEl.value = btn.dataset.q;
  formEl.requestSubmit();
});

formEl.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = inputEl.value.trim();
  if (!question) return;
  await askQuestion(question);
});

newChatBtn.addEventListener("click", () => {
  qaScrollEl.innerHTML = "";
  stageEl.classList.remove("chat-active");
  newChatBtn.hidden = true;
  inputEl.focus();
});

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function escapeAttr(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// Basit markdown: **kalın**, paragraflar, [N] atıfları rozet olarak, ve
// "Kaynak Alıntıları:" bölümünü gövdeden ayırır.
function renderAnswerBody(rawText) {
  const splitIdx = rawText.search(/Kaynak Alıntıları:?/i);
  const mainText = splitIdx >= 0 ? rawText.slice(0, splitIdx).trim() : rawText.trim();

  const paragraphs = mainText
    .split(/\n{1,}/)
    .map((p) => p.trim())
    .filter(Boolean);

  return paragraphs
    .map((p) => {
      let html = escapeHtml(p).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
      html = html.replace(/\[(\d+)\]/g, '<span class="cite">$1</span>');
      return `<p>${html}</p>`;
    })
    .join("");
}

function renderSources(sources) {
  return sources
    .map((s, i) => {
      const loc = ["Madde " + s.madde_no, s.fikra_no ? `fıkra (${s.fikra_no})` : null, s.bent_no ? `bent ${s.bent_no})` : null]
        .filter(Boolean)
        .join(", ");
      return `
        <div class="source-card">
          <div class="source-head">
            <span class="idx">[${i + 1}]</span>
            <span class="loc">${escapeHtml(loc)}</span>
            <span class="title">${escapeHtml(s.doc_title)}</span>
          </div>
          <div class="source-text">${escapeHtml(s.text)}</div>
        </div>`;
    })
    .join("");
}

qaScrollEl.addEventListener("click", (e) => {
  const toggle = e.target.closest(".sources-toggle");
  if (toggle) {
    toggle.classList.toggle("open");
    toggle.nextElementSibling.classList.toggle("open");
    return;
  }
  const copyBtn = e.target.closest("[data-copy]");
  if (copyBtn) {
    navigator.clipboard?.writeText(copyBtn.dataset.copy);
    copyBtn.classList.add("active");
    setTimeout(() => copyBtn.classList.remove("active"), 900);
    return;
  }
  const voteBtn = e.target.closest("[data-vote]");
  if (voteBtn) {
    const row = voteBtn.parentElement;
    row.querySelectorAll("[data-vote]").forEach((b) => b.classList.remove("active"));
    voteBtn.classList.add("active");
    return;
  }
  const retryBtn = e.target.closest("[data-retry]");
  if (retryBtn) {
    askQuestion(retryBtn.dataset.retry);
  }
});

async function askQuestion(question) {
  stageEl.classList.add("chat-active");
  newChatBtn.hidden = false;

  const block = document.createElement("div");
  block.className = "qa-block";
  block.innerHTML = `
    <div class="q-bubble-row"><div class="q-bubble">${escapeHtml(question)}</div></div>
    <div class="answer-block">
      <div class="thinking">
        <div class="thinking-dots"><span></span><span></span><span></span></div>
        <span>Kaynaklar taranıyor…</span>
      </div>
    </div>`;
  qaScrollEl.appendChild(block);
  inputEl.value = "";
  inputEl.style.height = "auto";
  submitEl.disabled = true;
  block.scrollIntoView({ behavior: "smooth", block: "start" });

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `İstek başarısız (${res.status})`);
    }
    const data = await res.json();
    renderAnswer(block, question, data);
  } catch (err) {
    block.querySelector(".answer-block").innerHTML = `
      <div class="warning-line">HATA: ${escapeHtml(err.message || String(err))}</div>`;
  } finally {
    submitEl.disabled = false;
    inputEl.focus();
  }
}

function renderAnswer(block, question, data) {
  const isLow = data.confidence_level === "low";
  const bodyHtml = renderAnswerBody(data.answer);
  const rawForCopy = escapeAttr(data.answer);

  block.querySelector(".answer-block").innerHTML = `
    <div class="a-body">${bodyHtml}</div>
    ${data.warnings ? `<div class="warning-line">${escapeHtml(data.warnings)}</div>` : ""}

    <button type="button" class="sources-toggle">
      ${ICONS.chevron}
      <span>Kaynaklar (${data.sources.length})</span>
    </button>
    <div class="sources-list">${renderSources(data.sources)}</div>

    <div class="action-row">
      <button type="button" class="icon-btn" data-vote="up" title="Yararlı">${ICONS.up}</button>
      <button type="button" class="icon-btn" data-vote="down" title="Yararlı değil">${ICONS.down}</button>
      <button type="button" class="icon-btn" data-retry="${escapeAttr(question)}" title="Yeniden dene">${ICONS.retry}</button>
      <button type="button" class="icon-btn" data-copy="${rawForCopy}" title="Kopyala">${ICONS.copy}</button>
      <span class="confidence-note ${isLow ? "low" : ""}">
        <span class="led"></span>${isLow ? "Düşük güven" : "Yüksek güven"}
      </span>
    </div>
  `;
}