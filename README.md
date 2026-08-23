# Elektrik Dağıtım Mevzuat RAG Sistemi

EPDK (Enerji Piyasası Düzenleme Kurumu) mevzuatına kaynak göstererek erişim
sağlayan bir RAG (Retrieval-Augmented Generation) sistemi. Kullanıcının
sorduğu soruyu ilgili kanun/yönetmelik maddeleriyle eşleştirir, madde
numarası ve alıntı göstererek cevap üretir.

> **Not:** Bu sistem bilgilendirme amaçlıdır, hukuki tavsiye niteliği
> taşımaz. Bağlayıcı kararlar için ilgili mevzuatın güncel resmi metnine
> ve/veya bir uzmana başvurun.

## Ekran görüntüleri

| Arayüz | Örnek cevap |
|---|---|
| ![Arayüz](docs/screenshots/arayuz.png) | ![Cevap](docs/screenshots/cevap.png) |

## Pipeline


- **Ingestion:** `src/ingestion/` — kaynak URL listesinden belge indirir,
  her indirmeden önce `robots.txt` kontrolü yapar, SHA-256 hash ile
  `data/raw/manifest.json`'a kaydeder.
- **Parsing:** `src/parsing/` — PDF/DOCX belgelerden madde bazlı yapılandırılmış
  metin çıkarır.
- **Embedding:** `src/embedding/` — `intfloat/multilingual-e5-base` modeliyle
  embedding üretir, Chroma vektör veritabanında saklar.
- **Retrieval:** `src/retrieval/` — BM25 + vektör aramayı birleştiren hibrit
  arama, ardından `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` ile reranking.
- **Generation:** `src/generation/` — Groq API üzerinden, sadece getirilen
  kaynaklara dayanarak (citation guard ile doğrulanmış) cevap üretir.
- **Tagging:** `src/tagging/` — madde metinlerini senaryo bazlı etiketler.
- **Web:** `web/` — FastAPI backend + statik frontend, sohbet arayüzü.

## Kurulum

### Yerel (venv)
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # GROQ_API_KEY gir
```

### Docker
```bash
docker compose up
```
İlk çalıştırmada embedding/reranker modelleri Hugging Face'ten inecek
(birkaç dakika sürebilir); model dosyaları bir Docker volume'ünde
önbelleğe alındığı için sonraki başlatmalarda tekrar inmez.

## Çalıştırma

```bash
python scripts/ingest.py        # mevzuatı indir
python scripts/parse.py         # PDF/DOCX'ten yapılandırılmış metin çıkar
python scripts/build_index.py   # embedding + BM25 index oluştur
python -m uvicorn web.app:app --reload   # web arayüzünü başlat
```
Arayüz: `http://localhost:8000`

## Değerlendirme
```bash
python scripts/run_eval.py
```
Sonuçlar `eval/results.json`'a yazılır.

## Test
```bash
pytest tests/ -v
```

## Bilinen sınırlar
- `src/ingestion/sources.py` içindeki sabit URL listesi kullanılır
  (otomatik mevzuat keşfi yok).
- 4 kaynaktan 2'si (EPDK listeleme sayfası ve bilgi sayfaları) otomatik
  çözümlenmiyor — bkz. `sources.py` içindeki `needs_resolution` notları.

## Lisans
MIT — bkz. [LICENSE](LICENSE)