new_html = """<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Mevzuat Asistani - Elektrik Dagitim</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="/static/style.css" />
</head>
<body>
<div class="app-shell">

  <aside class="left-rail">
    <div class="rail-brand">
      <svg class="brand-mark" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M13 2 L4 13 H10.5 L9 22 L20 9 H13.5 L13 2 Z" fill="currentColor"/>
      </svg>
      <span class="brand-word">Mevzuat<span class="brand-word-dim">Hat</span></span>
    </div>

    <button type="button" class="new-chat-btn" id="newChatBtn" hidden>
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
      Yeni sohbet
    </button>

    <div class="rail-section-label">Hizli sorular</div>
    <div class="quick-chips" id="quickChips">
      <button type="button" class="chip" data-q="Baglanti ve sistem kullanim anlasmasi nasil yapilir?">Baglanti talebi</button>
      <button type="button" class="chip" data-q="OSB katilimcilarinin sisteme baglantisi hangi mevzuata tabidir?">OSB baglantisi</button>
      <button type="button" class="chip" data-q="Kesinti suresi astiginda kullanicilara odenecek tazminat nasil hesaplanir?">Kesinti tazminati</button>
      <button type="button" class="chip" data-q="EV sarj hizmeti hangi lisans kapsaminda yurutulur?">EV sarj baglantisi</button>
    </div>

    <div class="rail-footer">
      <span class="rail-footer-note">EPDK mevzuatina dayanir. Hukuki tavsiye niteligi tasimaz.</span>
    </div>
  </aside>

  <main class="stage" id="stage">
    <section class="hero" id="hero">
      <div class="hero-mark-wrap" aria-hidden="true">
        <svg class="hero-mark" viewBox="0 0 100 100" fill="none">
          <path id="boltPath" d="M54 8 L20 54 H46 L38 92 L82 42 H56 L54 8 Z" fill="#4c8dff"/>
        </svg>
      </div>
      <h1 class="headline">Bugun size nasil yardimci olabilirim?</h1>
      <p class="subhead">EPDK mevzuati uzerinde arama yapar, her cevabi madde ve fikra
        referansiyla kaynaklandirir.</p>
    </section>

    <section class="conversation" id="conversation">
      <div class="qa-scroll" id="qaScroll"></div>
    </section>

    <div class="composer-dock" id="composerDock">
      <form class="ask-panel" id="askForm">
        <div class="ask-panel-inner">
          <textarea
            id="questionInput"
            class="ask-input"
            placeholder="Mevzuatla ilgili bir sey sorun..."
            rows="1"
            autocomplete="off"
          ></textarea>
          <button type="submit" class="ask-submit" id="askSubmit" aria-label="Gonder">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M12 19V5M12 5L6 11M12 5L18 11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </form>
    </div>
  </main>

  <aside class="source-panel" id="sourcePanel">
    <div class="source-panel-header">
      <span class="source-panel-title">Kaynakca</span>
      <span class="source-panel-count" id="sourcePanelCount"></span>
    </div>
    <div class="source-panel-body" id="sourcePanelBody">
      <div class="source-panel-empty" id="sourcePanelEmpty">
        Bir soru sordugunuzda, cevabin dayandigi madde ve fikralar burada listelenir.
      </div>
    </div>
  </aside>

</div>
<script src="/static/app.js"></script>
</body>
</html>
"""

with open("web/static/index.html", "w", encoding="utf-8") as f:
    f.write(new_html)
print("index.html yazildi, uzunluk:", len(new_html))
