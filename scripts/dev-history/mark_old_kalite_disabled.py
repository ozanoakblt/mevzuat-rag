import pathlib

p = pathlib.Path("src/ingestion/sources.py")
text = p.read_text(encoding="utf-8")

old = '''    SourceDoc(
        doc_id="yonetmelik-hizmet-kalitesi",
        title=(
            "Elektrik Dağıtımı ve Perakende Satışına İlişkin "
            "Hizmet Kalitesi Yönetmeliği (Son Versiyon)"
        ),
        url="https://www.epdk.gov.tr/Detay/Icerik/12-3/elektrik",
        fetch_type="needs_resolution",'''

new = '''    SourceDoc(
        doc_id="yonetmelik-hizmet-kalitesi",
        title=(
            "Elektrik Dağıtımı ve Perakende Satışına İlişkin "
            "Hizmet Kalitesi Yönetmeliği (ESKI/MULGA - yerine "
            "yonetmelik-kalite-guncel (Mevzuat No 36132) gecti)"
        ),
        url="https://www.epdk.gov.tr/Detay/Icerik/12-3/elektrik",
        fetch_type="disabled",'''

if old not in text:
    print("HATA: eslesme bulunamadi.")
else:
    new_text = text.replace(old, new)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili.")
