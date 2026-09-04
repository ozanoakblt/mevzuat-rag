new_css = """

/* ============================================================
   3 panelli duzen: sol rail + orta sohbet + sag kaynakca paneli
   ============================================================ */
body {
  height: 100vh;
  overflow: hidden;
  display: block;
}

.app-shell {
  height: 100vh;
  display: grid;
  grid-template-columns: 236px minmax(0, 1fr) 360px;
  overflow: hidden;
}

/* ---------- Sol rail ---------- */
.left-rail {
  border-right: 1px solid var(--border);
  background: var(--bg-elevated);
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding: 22px 16px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--border-strong) transparent;
}

.rail-brand { display: flex; align-items: center; gap: 8px; padding: 0 4px; }

.new-chat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: var(--accent-soft);
  border: 1px solid var(--border);
  color: var(--accent);
  font-size: 13px;
  font-weight: 600;
  padding: 10px 14px;
  border-radius: var(--r-md);
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}
.new-chat-btn[hidden] { display: none; }
.new-chat-btn:hover { background: rgba(91, 157, 255, 0.22); border-color: var(--accent); }
.new-chat-btn svg { width: 15px; height: 15px; }

.rail-section-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-faint);
  font-weight: 600;
  padding: 0 4px;
}

.left-rail .quick-chips {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: -8px;
}

.left-rail .quick-chips .chip {
  text-align: left;
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-dim);
  font-size: 13px;
  padding: 9px 10px;
  border-radius: var(--r-sm);
  width: 100%;
}
.left-rail .quick-chips .chip:hover {
  background: var(--bg);
  border-color: var(--border);
  color: var(--text);
}

.rail-footer {
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}
.rail-footer-note { font-size: 11px; line-height: 1.55; color: var(--text-faint); }

/* ---------- Orta sohbet kolonu ---------- */
.stage {
  max-width: none;
  width: 100%;
  padding: 0 28px;
  overflow: hidden;
}

.stage .hero,
.stage .qa-scroll,
.stage .composer-dock > * {
  max-width: 700px;
  margin-left: auto;
  margin-right: auto;
  width: 100%;
}

/* ---------- Sag kaynakca paneli ---------- */
.source-panel {
  border-left: 1px solid var(--border);
  background: var(--bg-elevated);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.source-panel-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 20px 16px;
  border-bottom: 1px solid var(--border);
}
.source-panel-title {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.01em;
  color: var(--text);
}
.source-panel-count {
  font-size: 11.5px;
  color: var(--text-faint);
  font-family: var(--font-mono);
}

.source-panel-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  scrollbar-width: thin;
  scrollbar-color: var(--border-strong) transparent;
}

.source-panel-empty {
  color: var(--text-faint);
  font-size: 13px;
  line-height: 1.6;
  padding: 8px 2px;
}

.source-panel-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  border-radius: var(--r-md);
  padding: 13px 15px;
}

.source-panel-card .card-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
}

.source-panel-card .idx-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: var(--accent-soft);
  color: var(--accent);
  border-radius: var(--r-pill);
  font-size: 11px;
  font-weight: 700;
  font-family: var(--font-mono);
  flex-shrink: 0;
}

.source-panel-card .loc {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text);
  font-weight: 600;
}

.source-panel-card .doc-title {
  display: block;
  margin-top: 3px;
  font-size: 11.5px;
  color: var(--text-faint);
}

.source-panel-card .body-text {
  margin-top: 10px;
  font-size: 12.8px;
  line-height: 1.65;
  color: var(--text-dim);
}

/* Genis ekranda satir ici kaynak listesi gizli - tek kaynak sag panel */
@media (min-width: 1181px) {
  .sources-toggle, .sources-list { display: none !important; }
}

/* Dar ekranlarda sag panel kaybolur, satir ici liste geri doner */
@media (max-width: 1180px) {
  .app-shell { grid-template-columns: 208px minmax(0, 1fr); }
  .source-panel { display: none; }
}
@media (max-width: 760px) {
  .app-shell { grid-template-columns: 1fr; }
  .left-rail { display: none; }
}
"""

with open("web/static/style.css", "a", encoding="utf-8") as f:
    f.write(new_css)
print("style.css guncellendi, eklenen uzunluk:", len(new_css))
