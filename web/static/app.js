const stageEl = document.querySelector(".stage");
const qaScrollEl = document.getElementById("qaScroll");
const formEl = document.getElementById("askForm");
const inputEl = document.getElementById("questionInput");
const submitEl = document.getElementById("askSubmit");
const chipsEl = document.getElementById("quickChips");
const newChatBtn = document.getElementById("newChatBtn");
const conversationEl = document.getElementById("conversation");
const historyListEl = document.getElementById("historyList");
let currentBlockEl = null;

const ICONS = {
  copy: `<svg viewBox="0 0 24 24" fill="none"><rect x="9" y="9" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.6"/><path d="M5 15V5a2 2 0 0 1 2-2h10" stroke="currentColor" stroke-width="1.6"/></svg>`,
  retry: `<svg viewBox="0 0 24 24" fill="none"><path d="M3 12a9 9 0 1 1 3 6.7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M3 21v-6h6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  up: `<svg viewBox="0 0 24 24" fill="none"><path d="M7 10v11H3V10h4Zm4 11h7.5a2 2 0 0 0 2-1.7l1.2-8a2 2 0 0 0-2-2.3H14V5a3 3 0 0 0-3-3l-2 7v12Z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg>`,
  down: `<svg viewBox="0 0 24 24" fill="none"><path d="M17 14V3h4v11h-4Zm-4-11H5.5a2 2 0 0 0-2 1.7l-1.2 8a2 2 0 0 0 2 2.3H10v4a3 3 0 0 0 3 3l2-7V3Z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg>`,
  chevron: `<svg viewBox="0 0 24 24" fill="none"><path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
};

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
  startNewConversation();
  inputEl.focus();
});

document.querySelectorAll(".rail-section-toggle").forEach((toggle) => {
  toggle.addEventListener("click", () => {
    const expanded = toggle.getAttribute("aria-expanded") !== "false";
    toggle.setAttribute("aria-expanded", expanded ? "false" : "true");
  });
});

/* ============================================================
   Gecmis sohbetler (localStorage) - bu tarayicida/cihazda kalir,
   sunucuya gonderilmez.
   ============================================================ */
const HISTORY_KEY = "mevzuatHat.history";
const HISTORY_LIMIT = 30;
let currentConversation = { id: null, title: null, turns: [] };

function loadHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveHistory(list) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(0, HISTORY_LIMIT)));
  } catch {
    /* localStorage dolu/erisilemez olabilir - sessizce yut, ozellik devre disi kalir */
  }
}

function renderHistoryList() {
  const list = loadHistory();
  const emptyEl = document.getElementById("historyEmpty");
  if (!list.length) {
    historyListEl.innerHTML = `<div class="history-empty" id="historyEmpty">Henuz gecmis sohbet yok.</div>`;
    return;
  }
  historyListEl.innerHTML = list
    .map(
      (c) => `<button type="button" class="history-item${c.id === currentConversation.id ? " active" : ""}" data-history-id="${escapeAttr(c.id)}" title="${escapeAttr(c.title)}">${escapeHtml(c.title)}</button>`
    )
    .join("");
}

function startNewConversation() {
  currentConversation = { id: null, title: null, turns: [] };
  qaScrollEl.innerHTML = "";
  stageEl.classList.remove("chat-active");
  resetSourcePanel();
  renderHistoryList();
}

function persistCurrentTurn(question, data) {
  if (!currentConversation.id) {
    currentConversation.id = String(Date.now());
    currentConversation.title = question.length > 60 ? question.slice(0, 57) + "…" : question;
  }
  currentConversation.turns.push({ question, data });

  const list = loadHistory().filter((c) => c.id !== currentConversation.id);
  list.unshift({ ...currentConversation });
  saveHistory(list);
  renderHistoryList();
}

function loadConversation(id) {
  const list = loadHistory();
  const conv = list.find((c) => c.id === id);
  if (!conv) return;

  currentConversation = { id: conv.id, title: conv.title, turns: [...conv.turns] };
  qaScrollEl.innerHTML = "";
  stageEl.classList.add("chat-active");
  conv.turns.forEach(({ question, data }) => {
    const block = appendQaBlock(question);
    renderAnswer(block, question, data);
  });
  resetSourcePanel();
  const lastTurn = conv.turns[conv.turns.length - 1];
  if (lastTurn) {
    renderSourcePanel(lastTurn.data.sources, qaScrollEl.lastElementChild, lastTurn.data.confidence_level === "low");
  }
  renderHistoryList();
  qaScrollEl.lastElementChild?.scrollIntoView({ behavior: "smooth", block: "start" });
}

historyListEl.addEventListener("click", (e) => {
  const item = e.target.closest(".history-item");
  if (!item) return;
  loadConversation(item.dataset.historyId);
});

renderHistoryList();

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

function renderInlineMarkdown(text) {
  let html = escapeHtml(text).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\[(\d+)\]/g, '<span class="cite" data-cite="$1">$1</span>');
  return html;
}

const _BULLET_RE = /^[-*]\s+(.*)$/;
const _ORDERED_RE = /^\d+[.)]\s+(.*)$/;

function renderAnswerBody(rawText) {
  const splitIdx = rawText.search(/Kaynak Alıntıları:?/i);
  let mainText = splitIdx >= 0 ? rawText.slice(0, splitIdx).trim() : rawText.trim();

  const lines = mainText.split(/\n+/);
  while (lines.length && /^[\s#*\-_]*$/.test(lines[lines.length - 1])) {
    lines.pop();
  }
  mainText = lines.join("\n").trim();

  const blockLines = mainText
    .split(/\n{1,}/)
    .map((l) => l.trim())
    .filter(Boolean);

  // Ardisik "- " / "* " / "1. " satirlarini TEK bir <ul>/<ol> blogunda
  // grupla - eskiden her satir ayri bir <p> oluyordu, liste isareti
  // (-/*) duz metin olarak gorunuyordu (gercek bir vakada tespit edildi:
  // "- SBSAYI: 0 TL ..." gibi tanim listeleri cirkin duz paragraflar
  // olarak basiliyordu).
  const htmlParts = [];
  let i = 0;
  while (i < blockLines.length) {
    const line = blockLines[i];
    const bulletMatch = line.match(_BULLET_RE);
    const orderedMatch = !bulletMatch && line.match(_ORDERED_RE);

    if (bulletMatch || orderedMatch) {
      const re = bulletMatch ? _BULLET_RE : _ORDERED_RE;
      const tag = bulletMatch ? "ul" : "ol";
      const items = [];
      while (i < blockLines.length) {
        const m = blockLines[i].match(re);
        if (!m) break;
        items.push(`<li>${renderInlineMarkdown(m[1])}</li>`);
        i += 1;
      }
      htmlParts.push(`<${tag}>${items.join("")}</${tag}>`);
    } else {
      htmlParts.push(`<p>${renderInlineMarkdown(line)}</p>`);
      i += 1;
    }
  }

  return htmlParts.join("");
}

function renderSuggestions(questions) {
  if (!questions || !questions.length) return "";
  const chips = questions
    .map((q) => `<button type="button" class="suggest-chip" data-suggest="${escapeAttr(q)}">${escapeHtml(q)}</button>`)
    .join("");
  return `
    <div class="suggest-box">
      <div class="suggest-title">Bunu mu sormak istediniz?</div>
      <div class="suggest-list">${chips}</div>
    </div>`;
}

function renderMathIn(el) {
  // KaTeX auto-render scriptleri `defer` ile yukleniyor - cok nadir bir
  // yaris durumunda (ilk cevap, script tam yuklenmeden gelirse) sessizce
  // atla, uygulamayi kilitleme.
  if (typeof window.renderMathInElement !== "function") return;
  try {
    window.renderMathInElement(el, {
      delimiters: [
        { left: "$$", right: "$$", display: true },
        { left: "\\[", right: "\\]", display: true },
        { left: "$", right: "$", display: false },
        { left: "\\(", right: "\\)", display: false },
      ],
      throwOnError: false,
    });
  } catch (err) {
    // KaTeX render hatasi (bozuk/yarim LaTeX) cevabi ham metin olarak
    // birakir - sessizce yutuluyor, kullaniciyi engellemez.
  }
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

function resetSourcePanel() {
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
    const block = voteBtn.closest(".qa-block");
    const fb = block && blockFeedbackData.get(block);
    if (fb) {
      fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...fb, vote: voteBtn.dataset.vote }),
      }).catch(() => {
        /* geri bildirim gonderilemezse sessizce yut - kullanicinin akisini bozma */
      });
    }
    return;
  }
  const suggestBtn = e.target.closest("[data-suggest]");
  if (suggestBtn) {
    askQuestion(suggestBtn.dataset.suggest);
    return;
  }
  const retryBtn = e.target.closest("[data-retry]");
  if (retryBtn) {
    askQuestion(retryBtn.dataset.retry);
    return;
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
});

function appendQaBlock(question) {
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
  return block;
}

async function askQuestion(question) {
  stageEl.classList.add("chat-active");
  // "generating" class'i 3 panelde de (sol rail/orta stage/sag kaynakca)
  // senkronize ambiyans glow animasyonunu tetikler (bkz. style.css
  // "Uretim ambiyans efekti" bolumu) - cevap uretimi bitince (basarili ya
  // da hatali fark etmez, finally'de) mutlaka kaldirilir.
  document.body.classList.add("generating");

  const block = appendQaBlock(question);
  inputEl.value = "";
  inputEl.style.height = "auto";
  submitEl.disabled = true;
  block.scrollIntoView({ behavior: "smooth", block: "start" });
  showSourcePanelSkeleton();

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
    persistCurrentTurn(question, data);
  } catch (err) {
    block.querySelector(".answer-block").innerHTML = `
      <div class="warning-line">HATA: ${escapeHtml(err.message || String(err))}</div>`;
  } finally {
    document.body.classList.remove("generating");
    submitEl.disabled = false;
    inputEl.focus();
  }
}

// Oy butonlarina basildiginda /api/feedback'e gonderilecek veriyi tutar -
// eskiden bu butonlar sadece gorsel bir CSS class toggle'iydi, hicbir
// yere kaydedilmiyordu (gercek kullanim geri bildirimi tamamen kayboluyordu).
const blockFeedbackData = new WeakMap();

function renderAnswer(block, question, data) {
  const isLow = data.confidence_level === "low";
  blockFeedbackData.set(block, {
    question,
    answer: data.answer,
    confidence_level: data.confidence_level,
    source_count: data.sources.length,
  });
  const bodyHtml = renderAnswerBody(data.answer);
  const rawForCopy = escapeAttr(data.answer);
  renderSourcePanel(data.sources, block, isLow);

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
    ${renderSuggestions(data.suggested_questions)}
  `;
  renderMathIn(block.querySelector(".a-body"));
}
