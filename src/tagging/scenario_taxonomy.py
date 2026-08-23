"""Brief madde 9: senaryo taksonomisi (sabit sözlük).

Hem dokümanlar hem sorgular AYNI listeden etiketlenir. Yeni etiket eklemek
isterseniz sadece bu listeyi güncelleyin — tagger ve query analysis
otomatik olarak senkron kalır.
"""

SCENARIO_TAXONOMY: dict[str, str] = {
    "baglanti_talebi": "Bağlantı talebi / sistem kullanım anlaşması",
    "osb_baglantisi": "OSB / endüstri bölgesi bağlantısı",
    "topraklama_izolasyon": "Topraklama ve izolasyon uygunluğu",
    "kesinti_tazminat": "Kesinti süresi ve tazminat (SAIDI/SAIFI)",
    "sayac_arizasi": "Sayaç arızası / ölçüm anlaşmazlığı",
    "gerilim_kalitesi": "Gerilim kalitesi şikâyeti (flicker, harmonik, gerilim düşümü)",
    "dagitik_uretim": "Dağıtılmış üretim (GES/RES) bağlantısı",
    "ev_sarj": "EV şarj istasyonu bağlantısı",
    "kayip_kacak": "Kayıp-kaçak bedeli / yüksek kayıplı bölge uygulaması",
    "trafo_kapasite": "Trafo merkezi kapasite artırımı",
    "gecici_baglanti": "Geçici bağlantı (şantiye vb.)",
    "tarife_degisikligi": "Tarife / abone grubu değişikliği",
    "sistem_kullanim_bedeli": "Sistem kullanım bedeli hesaplama",
    "isletme_sinirlari": "İşletme sınırları ve bakım sorumluluğu",
    "mulkiyet_devri": "Kullanıcı mülkiyetindeki tesislerin devri",
    "acil_mudahale": "Acil müdahale / arıza giderme süreleri",
    "cbs_yukumlulukleri": "CBS (coğrafi bilgi sistemi) yükümlülükleri",
}

# Prompt için hazır liste metni (id: açıklama satırları).
TAXONOMY_PROMPT_LIST = "\n".join(f"- {k}: {v}" for k, v in SCENARIO_TAXONOMY.items())

VALID_TAGS = set(SCENARIO_TAXONOMY.keys())
