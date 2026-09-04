import pathlib

p = pathlib.Path("src/generation/citation_guard.py")
text = p.read_text(encoding="utf-8")

old = '''_TURKISH_NUMBER_WORDS = {
    "sifir": "0", "bir": "1", "iki": "2", "uc": "3", "dort": "4",
    "bes": "5", "alti": "6", "yedi": "7", "sekiz": "8", "dokuz": "9",
    "on": "10", "yirmi": "20", "otuz": "30", "kirk": "40", "elli": "50",
    "altmis": "60", "yetmis": "70", "seksen": "80", "doksan": "90",
    "yuz": "100", "bin": "1000",
}'''

new = '''_TURKISH_NUMBER_WORDS = {
    "sıfır": "0", "bir": "1", "iki": "2", "üç": "3", "dört": "4",
    "beş": "5", "altı": "6", "yedi": "7", "sekiz": "8", "dokuz": "9",
    "on": "10", "yirmi": "20", "otuz": "30", "kırk": "40", "elli": "50",
    "altmış": "60", "yetmiş": "70", "seksen": "80", "doksan": "90",
    "yüz": "100", "bin": "1000",
}'''

if old not in text:
    print("HATA: eslesme bulunamadi.")
else:
    new_text = text.replace(old, new)
    p.write_text(new_text, encoding="utf-8")
    print("Basarili.")
