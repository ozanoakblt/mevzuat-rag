"""
Faz 2: Metadata şeması (brief madde 7) ve chunk üretimi (brief madde 8).

Chunk üretim önceliği: Bent varsa bent, yoksa fıkra, yoksa madde bütünü.
Her chunk'ın embedding_text alanı, brief'in "context'i kaybetmemeli" isteği
gereği belge adı > bölüm > madde başlığı > fıkra/bent numarası zincirini
başa ekler.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .structure_parser import MaddeBlock, parse_document


@dataclass
class DocumentMetadata:
    doc_id: str
    title: str
    doc_type: str  # "kanun" | "yonetmelik" | "yonetmelik_degisiklik"
    status: str = "active"  # "active" | "repealed" (versiyonlama sonraki fazda)
    law_or_reg_no: str | None = None  # ör. "6446"
    publish_date: str | None = None  # RG tarihi, tespit edilebilirse
    rg_sayi: str | None = None
    source_local_path: str = ""
    sha256: str = ""
    completeness_note: str = ""  # SourceDoc'tan taşınır (bkz. sources.py)
    related_documents: list[str] = field(default_factory=list)
    parsed_at: str = ""
    appendices: list[dict] = field(default_factory=list)  # bkz. _split_appendix


@dataclass
class ChunkRecord:
    chunk_id: str
    doc_id: str
    madde_kind: str
    madde_no: str
    madde_baslik: str | None
    bolum: str | None
    fikra_no: str | None
    bent_no: str | None
    section: str | None  # "Tanımlar" gibi özel etiket
    text: str
    embedding_text: str
    amendment_refs: list[str] = field(default_factory=list)
    scenario_tags: list[str] = field(default_factory=list)


def _embedding_prefix(doc_title: str, block: MaddeBlock) -> str:
    parts = [doc_title]
    if block.bolum:
        parts.append(block.bolum)
    madde_label = f"{block.madde_kind} {block.madde_no}"
    if block.madde_baslik:
        madde_label += f" ({block.madde_baslik})"
    parts.append(madde_label)
    return " > ".join(parts)


_KIND_PREFIX = {"MADDE": "m", "GEÇİCİ MADDE": "gm", "EK MADDE": "em"}

# Bir fıkranın bentleri ortalama bu karakter sayısının altındaysa (ör.
# "a) Üretim faaliyeti" gibi bir madde listesi), bentlere AYRI AYRI
# chunk açmak yerine tüm fıkrayı TEK chunk olarak tutuyoruz. Sebep:
# Faz "sistemi iyileştirelim" turunda gerçek eval verisiyle bulundu —
# "Üretim faaliyeti" gibi 2-3 kelimelik bir bent metni, embedding için
# yeterince zengin bağlam taşımıyor, retrieval'da neredeyse hiç
# bulunamıyordu (bkz. README "Reranker Güvenlik Ağı" bölümündeki q02
# vakası). Fıkra bütünü halinde ("Piyasada faaliyetler: a) Üretim
# faaliyeti b) İletim faaliyeti ...") çok daha zengin bir embedding
# oluşuyor ve "faaliyetler nelerdir" gibi sorularla doğru eşleşiyor.
SHORT_BENT_AVG_CHAR_THRESHOLD = 40


def _bents_are_short_list(fikra) -> bool:
    if not fikra.bents:
        return False
    avg_len = sum(len(b.text) for b in fikra.bents) / len(fikra.bents)
    return avg_len < SHORT_BENT_AVG_CHAR_THRESHOLD


def _chunk_id_prefix(doc_id: str, block: MaddeBlock) -> str:
    kind_prefix = _KIND_PREFIX.get(block.madde_kind, "m")
    # madde_no içindeki "/" gibi karakterler chunk_id'yi bozmasın diye korunuyor,
    # sadece kind ayrımı ekleniyor (asıl çakışma sebebi buydu).
    return f"{doc_id}::{kind_prefix}{block.madde_no}"


# Embedding modeli (multilingual-e5-base) 512 token limitine sahip; gercek
# olcumle Turkce mevzuat metninde ~4.4 karakter/token (bkz. kanun-4628::m5
# testi: 11423 karakter = 2596 token). Bu esigin UZERINDEKI bir chunk
# SentenceTransformer tarafindan sessizce KESILIR - iceriginin sonu hic
# embed edilmez, dense retrieval o kismi asla bulamaz (BM25/sparse
# etkilenmez, tam metni goruyor, bu yuzden sorun tamamen gorunmez kalabilir).
# Gercek bir vakada tespit edildi: korpusun >%3'u (1103 chunk) bu esigi
# asiyordu, bazilari 20K+ karakter. 1800 karakter (~410 token), embedding_
# text'in basina eklenen prefix (belge>bolum>madde basligi) icin pay
# birakarak 512 token siniri altinda kalmayi garantiliyor.
_MAX_EMBEDDING_CHARS = 1800


def _greedy_join_split(pieces: list[str], max_chars: int) -> list[str]:
    """pieces'i, her parca en fazla max_chars olacak sekilde acgozlu birlestirir."""
    parts: list[str] = []
    current = ""
    for piece in pieces:
        if current and len(current) + len(piece) + 1 > max_chars:
            parts.append(current.strip())
            current = piece
        else:
            current = f"{current} {piece}".strip() if current else piece
    if current:
        parts.append(current.strip())
    return parts


def _split_text_into_parts(text: str, max_chars: int) -> list[str]:
    """
    Metni max_chars'i asmayan parcalara boler, kademeli olarak daha
    agresif ayiricilar dener: once cumle sinirlari (. ! ?), bu yetmezse
    (gercek bir vakada tespit edildi: bazi "Tanimlar" fikralari virgulle
    ayrilmis onlarca terimden olusur, neredeyse hic nokta icermez - tek
    bir "cumle" 21K+ karakter kaliyordu) virgul/noktali virgul, o da
    yetmezse SON CARE olarak sert karakter siniri (kelime ortasindan
    kesmek pahasina - bu, hicbir zaman embed edilmemekten iyidir).
    """
    if len(text) <= max_chars:
        return [text]
    import re

    for pattern in (r"(?<=[.!?])\s+", r"(?<=[,;])\s+"):
        pieces = re.split(pattern, text)
        if len(pieces) > 1:
            parts = _greedy_join_split(pieces, max_chars)
            if all(len(p) <= max_chars for p in parts):
                return parts

    # Son care: sert karakter siniri.
    return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]


def _split_oversized_chunks(chunks: list[ChunkRecord]) -> list[ChunkRecord]:
    result: list[ChunkRecord] = []
    for c in chunks:
        if len(c.embedding_text) <= _MAX_EMBEDDING_CHARS or not c.embedding_text.endswith(c.text):
            result.append(c)
            continue
        prefix = c.embedding_text[: len(c.embedding_text) - len(c.text)]
        text_parts = _split_text_into_parts(c.text, _MAX_EMBEDDING_CHARS - len(prefix))
        if len(text_parts) <= 1:
            result.append(c)
            continue
        for i, part in enumerate(text_parts, start=1):
            result.append(
                ChunkRecord(
                    chunk_id=f"{c.chunk_id}::p{i}",
                    doc_id=c.doc_id,
                    madde_kind=c.madde_kind,
                    madde_no=c.madde_no,
                    madde_baslik=c.madde_baslik,
                    bolum=c.bolum,
                    fikra_no=c.fikra_no,
                    bent_no=c.bent_no,
                    section=c.section,
                    text=part,
                    embedding_text=f"{prefix}{part}",
                    amendment_refs=c.amendment_refs if i == 1 else [],
                    scenario_tags=c.scenario_tags,
                )
            )
    return result


def build_chunks(doc_meta: DocumentMetadata, blocks: list[MaddeBlock]) -> list[ChunkRecord]:
    chunks: list[ChunkRecord] = []
    prefix_base = doc_meta.title
    seen_ids: dict[str, int] = {}

    def _unique(chunk_id: str) -> str:
        """
        Güvenlik ağı: parser'daki bir kenar-durum (ör. PDF'te tespit
        edilemeyen bir madde sınırı) aynı chunk_id'yi iki kez üretirse,
        sessizce veri kaybetmek ya da index'i çökertmek yerine sona
        "-2", "-3" gibi bir ayırt edici ekler. Bu, altta yatan ayrıştırma
        sorununu ÇÖZMEZ (o ayrı bir düzeltme gerektirir), sadece pipeline'ın
        kırılmadan devam etmesini sağlar.
        """
        seen_ids[chunk_id] = seen_ids.get(chunk_id, 0) + 1
        if seen_ids[chunk_id] == 1:
            return chunk_id
        return f"{chunk_id}-dup{seen_ids[chunk_id]}"

    for block in blocks:
        section = "Tanımlar" if block.is_tanimlar else None
        prefix = _embedding_prefix(prefix_base, block)
        id_prefix = _chunk_id_prefix(doc_meta.doc_id, block)

        if not block.fikralar:
            # Fıkraya bile ayrılamamışsa (nadir), madde bütünü tek chunk.
            chunk_id = _unique(id_prefix)
            chunks.append(
                ChunkRecord(
                    chunk_id=chunk_id,
                    doc_id=doc_meta.doc_id,
                    madde_kind=block.madde_kind,
                    madde_no=block.madde_no,
                    madde_baslik=block.madde_baslik,
                    bolum=block.bolum,
                    fikra_no=None,
                    bent_no=None,
                    section=section,
                    text=block.raw_text,
                    embedding_text=f"{prefix}: {block.raw_text}",
                )
            )
            continue

        for fikra in block.fikralar:
            if not fikra.bents or _bents_are_short_list(fikra):
                chunk_id = _unique(f"{id_prefix}::f{fikra.fikra_no}")
                # Kısa bent listesi olsa bile amendment_refs'i (varsa, o
                # fıkranın herhangi bir bendinden) kaybetmemek için topla.
                combined_amendment_refs = fikra.amendment_refs or [
                    ref for b in fikra.bents for ref in b.amendment_refs
                ]
                chunks.append(
                    ChunkRecord(
                        chunk_id=chunk_id,
                        doc_id=doc_meta.doc_id,
                        madde_kind=block.madde_kind,
                        madde_no=block.madde_no,
                        madde_baslik=block.madde_baslik,
                        bolum=block.bolum,
                        fikra_no=fikra.fikra_no,
                        bent_no=None,
                        section=section,
                        text=fikra.text,
                        embedding_text=f"{prefix}, fıkra ({fikra.fikra_no}): {fikra.text}",
                        amendment_refs=combined_amendment_refs,
                    )
                )
                continue

            for bent in fikra.bents:
                chunk_id = _unique(f"{id_prefix}::f{fikra.fikra_no}::b{bent.bent_no}")
                chunks.append(
                    ChunkRecord(
                        chunk_id=chunk_id,
                        doc_id=doc_meta.doc_id,
                        madde_kind=block.madde_kind,
                        madde_no=block.madde_no,
                        madde_baslik=block.madde_baslik,
                        bolum=block.bolum,
                        fikra_no=fikra.fikra_no,
                        bent_no=bent.bent_no,
                        section=section,
                        text=bent.text,
                        embedding_text=(
                            f"{prefix}, fıkra ({fikra.fikra_no}), "
                            f"bent {bent.bent_no}): {bent.text}"
                        ),
                        amendment_refs=bent.amendment_refs,
                    )
                )

    return _split_oversized_chunks(chunks)


import re as _re

_EK_HEADER_RE = _re.compile(r"^EK[\s-]?(\d{1,2})\b\s*[:\-\u2013]?\s*(.*)$", _re.IGNORECASE)
# Eskiden 4000'di - _MAX_EMBEDDING_CHARS ile ayni sebepten (512 token
# embedding siniri, bkz. o sabitin yorumu) kucultuldu, tutarlilik icin
# ayni degeri kullaniyor.
_EK_MAX_CHUNK_CHARS = _MAX_EMBEDDING_CHARS


def extract_appendices(raw_text: str) -> list[dict]:
    """
    Belgenin sonundaki "EK-1", "EK-18" gibi teknik ekleri (tablo, formul,
    baglanti kriterleri vb.) ayri, bagimsiz parcalar olarak cikarir.
    Bunlar madde/fikra/bent yapisina uymadigi icin parse_document()/
    build_chunks() tarafindan hic yakalanmiyordu (gercek bir vakada
    tespit edildi: Elektrik Sebeke Yonetmeligi'nde Ek-1..Ek-24 hicbir
    chunk'a girmemisti). Sadece BASLI BASINA KISA satirlari (baslik
    olma ihtimali yuksek, <80 karakter) sinir kabul ediyoruz - boylece
    cumle icinde gecen "...Ek-18'i..." gibi referanslari yanlislikla
    sinir saymiyoruz.
    """
    lines = raw_text.splitlines()
    boundaries: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        s = line.strip()
        if not s or len(s) >= 80:
            continue
        m = _EK_HEADER_RE.match(s)
        if m:
            boundaries.append((i, m.group(1)))

    appendices: list[dict] = []
    for idx, (line_idx, ek_no) in enumerate(boundaries):
        end = boundaries[idx + 1][0] if idx + 1 < len(boundaries) else len(lines)
        body = "\n".join(l.strip() for l in lines[line_idx:end] if l.strip())
        if len(body) < 30:
            continue
        if len(body) <= _EK_MAX_CHUNK_CHARS:
            appendices.append({"ek_no": ek_no, "part": None, "text": body})
        else:
            for part_idx, start in enumerate(range(0, len(body), _EK_MAX_CHUNK_CHARS), start=1):
                appendices.append(
                    {
                        "ek_no": ek_no,
                        "part": part_idx,
                        "text": body[start : start + _EK_MAX_CHUNK_CHARS],
                    }
                )
    return appendices


def parse_and_save(
    doc_meta: DocumentMetadata, raw_text: str, output_dir: str | Path
) -> Path:
    """Bir belgeyi ayrıştırır, chunk'lara böler ve JSON olarak kaydeder."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    blocks = parse_document(raw_text)
    doc_meta.parsed_at = datetime.now(timezone.utc).isoformat()
    doc_meta.appendices = [
        {"after_madde_no": b.madde_no, "text": b.trailing_appendix}
        for b in blocks
        if b.trailing_appendix
    ]
    chunks = build_chunks(doc_meta, blocks)

    # Bazi "karar" tipi belgeler (ozellikle yillik ucret/bedel guncelleme
    # Kurul Kararlari) MADDE basligi hic kullanmaz - tek bir "... karar
    # verilmistir" cumlesi + bir tablo. parse_document() boyle belgelerde
    # 0 blok doner ve belge sessizce indeksten duser (chunk_count=0). Bu,
    # tam da bu tur belgelerin tasidigi guncel sayisal degerleri (ornegin
    # yillik bedel tablosu) aramadan tamamen kaybeder. MADDE-yapili
    # belgeler icin bu fallback devreye girmez (blocks bos degilse
    # atlanir), sadece yapisiz "karar" belgeleri icin tum metni tek bir
    # chunk olarak korur.
    if not blocks and doc_meta.doc_type == "karar" and raw_text.strip():
        fallback_text = raw_text.strip()
        fallback_prefix = f"{doc_meta.title}: "
        chunks = _split_oversized_chunks(
            [
                ChunkRecord(
                    chunk_id=f"{doc_meta.doc_id}::tam",
                    doc_id=doc_meta.doc_id,
                    madde_kind="BELGE",
                    madde_no="-",
                    madde_baslik=None,
                    bolum=None,
                    fikra_no=None,
                    bent_no=None,
                    section=None,
                    text=fallback_text,
                    embedding_text=f"{fallback_prefix}{fallback_text}",
                )
            ]
        )

    appendix_records = extract_appendices(raw_text)
    appendix_chunks: list[ChunkRecord] = []
    for i, ap in enumerate(appendix_records):
        suffix = f"-p{ap['part']}" if ap["part"] else ""
        chunk_id = f"{doc_meta.doc_id}::ek{ap['ek_no']}{suffix}"
        appendix_chunks.append(
            ChunkRecord(
                chunk_id=chunk_id,
                doc_id=doc_meta.doc_id,
                madde_kind="EK",
                madde_no=f"Ek-{ap['ek_no']}",
                madde_baslik=None,
                bolum=None,
                fikra_no=None,
                bent_no=None,
                section="Ek",
                text=ap["text"],
                embedding_text=f"{doc_meta.title} > Ek-{ap['ek_no']}: {ap['text']}",
            )
        )
    # extract_appendices kendi (daha kaba, karakter-siniri) on-bolmesini
    # yapar ama embedding_text prefix'ini (baslik > Ek-N:) hesaba katmaz -
    # sonuc yine de _MAX_EMBEDDING_CHARS'i asabilir. Ayni cumle-tabanli
    # bolme mantigini burada da uygulayarak garanti altina aliyoruz.
    chunks.extend(_split_oversized_chunks(appendix_chunks))

    out = {
        "document": asdict(doc_meta),
        "chunk_count": len(chunks),
        "madde_count": len(blocks),
        "maddeler": [
            {
                "madde_no": b.madde_no,
                "madde_kind": b.madde_kind,
                "madde_baslik": b.madde_baslik,
                "bolum": b.bolum,
                "full_text": b.raw_text,
            }
            for b in blocks
        ],
        "chunks": [asdict(c) for c in chunks],
    }
    out_path = output_dir / f"{doc_meta.doc_id}.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
