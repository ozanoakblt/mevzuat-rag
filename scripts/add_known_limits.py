import pathlib

p = pathlib.Path("README.md")
text = p.read_text(encoding="utf-8")

anchor = """## Bilinen sınırlar
- `src/ingestion/sources.py` içindeki sabit URL listesi kullanılır
  (otomatik mevzuat keşfi yok).
- 4 kaynaktan 2'si (EPDK listeleme sayfası ve bilgi sayfaları) otomatik
  çözümlenmiyor — bkz. `sources.py` içindeki `needs_resolution` notları."""

addition = anchor + """
- Coklu kaynak sentezi gerektiren sorularda (orn. iki kavrami
  karsilastirma, tablo olusturma) citation guard bazen bir veya birden
  fazla alintiyi "dogrulanamayan" olarak isaretliyor - model, sentez
  yaparken birebir alintidan paraphrase'e kayabiliyor. Tekil, dogrudan
  madde sorularinda bu sorun gorulmuyor.
- Koşullu/çok kriterli kurallarda (örn. güç esigi + konum birlikte
  degisen degerler) sistem artik bunlari "celiski" olarak yanlis
  etiketlemiyor (bkz. SYSTEM_PROMPT kural 5b/5c), ama bazen bir kosulu
  digerinin ozel hali gibi sunma riski hala tam ortadan kalkmis
  degil - karmasik, 3+ kriterli kurallarda dikkatli okunmali.
- Soru formulasyonuna retrieval performansi hassas olabiliyor; ayni
  konuyu farkli kelimelerle soran ozdes sorular farkli kaynak
  setleri getirebilir."""

if anchor not in text:
    print("HATA: anchor bulunamadi.")
else:
    new_text = text.replace(anchor, addition)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili.")
