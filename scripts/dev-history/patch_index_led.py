import pathlib

p = pathlib.Path("web/static/index.html")
text = p.read_text(encoding="utf-8")

old = """    <div class="source-panel-header">
      <span class="source-panel-title">Kaynakca</span>
      <span class="source-panel-count" id="sourcePanelCount"></span>
    </div>"""

new = """    <div class="source-panel-header">
      <div class="source-panel-title-row">
        <span class="source-panel-led" id="sourcePanelLed" hidden></span>
        <span class="source-panel-title">Kaynakca</span>
      </div>
      <span class="source-panel-count" id="sourcePanelCount"></span>
    </div>"""

if old not in text:
    print("HATA: eslesme bulunamadi (index.html).")
else:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("index.html guncellendi.")
