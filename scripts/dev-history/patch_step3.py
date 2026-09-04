import pathlib

p = pathlib.Path("web/static/app.js")
lines = p.read_text(encoding="utf-8").split("\n")

ok = True

# 1) satir 211 "});" -> retryBtn blogundan sonra hover/click davranisi ekle
idx1 = 211
if lines[idx1].strip() != "});":
    print("HATA 1: beklenen '});' bulunamadi, gercek:", repr(lines[idx1]))
    ok = False
else:
    lines[idx1] = """});

qaScrollEl.addEventListener("click", (e) => {
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

# 2) satir 228 "qaScrollEl.appendChild(block);" -> sonrasina skeleton cagrisi ekle
idx2 = 228
if "qaScrollEl.appendChild(block);" not in lines[idx2]:
    print("HATA 2: beklenen appendChild bulunamadi, gercek:", repr(lines[idx2]))
    ok = False
else:
    lines[idx2] = lines[idx2] + "\n  showSourcePanelSkeleton();"

# 3) satir 259 "renderSourcePanel(data.sources);" -> parametre ekle
idx3 = 259
if "renderSourcePanel(data.sources);" not in lines[idx3]:
    print("HATA 3: beklenen renderSourcePanel cagrisi bulunamadi, gercek:", repr(lines[idx3]))
    ok = False
else:
    lines[idx3] = lines[idx3].replace(
        "renderSourcePanel(data.sources);",
        "renderSourcePanel(data.sources, block, isLow);"
    )

if ok:
    p.write_text("\n".join(lines), encoding="utf-8")
    print("Basarili, uc degisiklik de uygulandi.")
else:
    print("En az bir hata oldu, dosya DEGISTIRILMEDI.")
