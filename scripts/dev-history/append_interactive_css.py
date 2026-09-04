new_css = """

/* ============================================================
   Ek: tiklanabilir/hover atif rozetleri, aktif kaynak vurgusu,
   iskelet (skeleton) yukleniyor durumu, guven gostergesi
   ============================================================ */
.a-body .cite {
  cursor: pointer;
  transition: background 0.12s ease, color 0.12s ease, transform 0.12s ease;
}
.a-body .cite:hover {
  background: var(--accent);
  color: #0b0d10;
  transform: scale(1.08);
}

.source-panel-card {
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}
.source-panel-card.hover-highlight {
  border-color: var(--accent);
  background: rgba(91, 157, 255, 0.05);
}
.source-panel-card.active-highlight {
  border-color: var(--accent);
  background: rgba(91, 157, 255, 0.08);
  box-shadow: 0 0 0 1px var(--accent), 0 4px 18px rgba(91, 157, 255, 0.12);
}

.source-panel-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.source-panel-led {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent);
  flex-shrink: 0;
}
.source-panel-led.low { background: var(--warn); }
.source-panel-led[hidden] { display: none; }

/* Iskelet (skeleton) kartlar - cevap uretilirken */
.source-skeleton-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-left: 3px solid var(--border-strong);
  border-radius: var(--r-md);
  padding: 13px 15px;
  overflow: hidden;
  position: relative;
}
.skeleton-line {
  height: 10px;
  border-radius: 5px;
  background: linear-gradient(
    90deg,
    var(--border) 0%,
    var(--border-strong) 50%,
    var(--border) 100%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.4s ease-in-out infinite;
  margin-bottom: 8px;
}
.skeleton-line.w-40 { width: 40%; height: 14px; }
.skeleton-line.w-70 { width: 70%; }
.skeleton-line.w-90 { width: 90%; }
.skeleton-line.w-60 { width: 60%; margin-bottom: 0; }

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton-line { animation: none; }
}
"""

with open("web/static/style.css", "a", encoding="utf-8") as f:
    f.write(new_css)
print("style.css guncellendi.")
