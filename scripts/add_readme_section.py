import pathlib

p = pathlib.Path("README.md")
raw = p.read_text(encoding="utf-8-sig")
try:
    raw = raw.encode("cp1252").decode("utf-8")
except (UnicodeEncodeError, UnicodeDecodeError):
    pass

new_section = """## Neden RAG, neden dogrudan bir LLM'e sormuyoruz?

Gelistirme surecinde ayni sorulari Gemini, ChatGPT ve DeepSeek'e de sorup
karsilastirdik. Sonuclar, kaynak gosteren bir RAG sisteminin neden gerekli
oldugunu somut ornekerle gosterdi:

**1) Genel modeller tutarsiz olabiliyor.** Ayni soruyu ("baglanti gorusu
gecerlilik suresi kac gun?") farkli oturumlarda ChatGPT'ye sorduk: bir
seferinde dogru cevabi (90 gun, 27 Ocak 2026 degisikligiyle guncellendi)
verdi, baska bir seferinde eski/yanlis bir rakam (60 gun) verdi - ayni
gun, ayni model. MevzuatRag sabit bir kaynaga (indirilen, versiyon
tarihli mevzuat metni) dayandigi icin bu tutarsizlik yapisal olarak
mumkun degil.

**2) Kaynak gosterilmeyince dogrulamak kullaniciya kaliyor.** Gemini ve
DeepSeek genelde dogru cevaplar verdi, ama madde numarasi veya alinti
olmadan - kullanicinin iddiayi ayrica arastirmasi gerekiyor. MevzuatRag
her cevaba madde/fikra numarasi ve resmi metinden birebir dogrulanmis
alinti ekliyor (bkz. `citation_guard.py`), boylece dogrulama sisteme
gomulu.

**3) Az bilinen detaylarda genel modeller bazen bosluk birakiyor.**
"Tedarikci ilk tuketiciyi portfoyune dahil ettiginde sistem kullanim
anlasmasi icin ne zamana kadar basvurmali?" sorusunda DeepSeek dogru
cevabi (ayin onuncu gunu) bulamadi ve kullaniciyi EPDK'ya yonlendirdi;
MevzuatRag ve Gemini dogru cevabi verdi, ama sadece MevzuatRag kaynak
gosterdi.

**4) Belirsiz/celiskili bir soruya verilen tepki fark yaratiyor.**
Kasitli olarak celiskili bir soru sorduk (AG seviyesi + tarimsal
faaliyet - kaynak metinde bu ikisi ayni fikrada gecmiyor). Gemini ve
DeepSeek soruyu sorgulamadan kendinden emin bir cevap verdi. MevzuatRag
ise "dusuk guven" ve "dogrulanamayan alinti" uyarisi verdi - sistem
kendi cevabindaki belirsizligi kullaniciya acikca bildirdi, sessizce
gecistirmedi.

**Ozet:** genel amacli LLM'ler cogu zaman dogru cevap veriyor, ama
*tutarliligi* ve *dogrulanabilirligi* garanti etmiyor. Mevzuat gibi
hukuki baglayiciligi olan, sik degisen bir alanda bu iki ozellik
(tutarlilik + dogrulanabilirlik) RAG mimarisinin asil katma degeri.

"""

marker = "## Kurulum"
idx = raw.index(marker)
new_raw = raw[:idx] + new_section + raw[idx:]

p.write_text(new_raw, encoding="utf-8")
print("Eklendi. Yeni uzunluk:", len(new_raw))
