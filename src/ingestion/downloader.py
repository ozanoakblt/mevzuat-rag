"""
Faz 1: indirme + hashleme.

Kurallar (brief madde 2, 6):
  - Her istekten önce ilgili domain'in robots.txt'i kontrol edilir.
    Disallow varsa indirme YAPILMAZ, kullanıcıya bildirilir.
  - İstekler arası makul bekleme (INGEST_REQUEST_DELAY_SECONDS, varsayılan 3sn).
  - Şeffaf bir User-Agent gönderilir (kim olduğumuzu ve amacımızı belirtir).
  - Hash aynıysa: logla, atla. Farklıysa: yeni sürüm olarak kaydet
    (versiyon geçmişi ayrı bir modülde ele alınacak — Faz 1'de sadece
    tekil indirme + hash kaydı var, "eski sürümü repealed işaretleme"
    mantığı brief madde 6/11'e göre sonraki fazda).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import urllib.robotparser
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

from .sources import SourceDoc

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    "mevzuat-rag-internal-tool/0.1 (sirket ici arastirma araci; "
    "otomatik degil, dusuk hizli, tek seferlik indirme)"
)
DEFAULT_DELAY_SECONDS = 3.0


class RobotsDisallowedError(Exception):
    """Hedef URL için robots.txt otomatik erişime izin vermiyor."""


_CONTENT_TYPE_EXT_MAP = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


def _guess_extension(content_type: str, url: str) -> str:
    ct = content_type.lower().split(";")[0].strip()
    if ct in _CONTENT_TYPE_EXT_MAP:
        return _CONTENT_TYPE_EXT_MAP[ct]
    # Content-Type belirsizse (ör. sunucu octet-stream döndürüyorsa) URL uzantısına bak.
    for ext in (".pdf", ".docx", ".doc"):
        if url.lower().endswith(ext):
            return ext
    return ".html" if "html" in ct else ".bin"


def _robots_allows(url: str, user_agent: str, timeout: float = 10.0) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    try:
        # RobotFileParser.read() kendi timeout'unu desteklemiyor (sonsuza kadar
        # asılı kalabilir) — bu yüzden içeriği requests ile (timeout'lu) çekip
        # parse() ile besliyoruz.
        resp = requests.get(robots_url, headers={"User-Agent": user_agent}, timeout=timeout)
        if resp.status_code == 404:
            # robots.txt yoksa: varsayılan olarak izin var kabul edilir.
            return True
        resp.raise_for_status()
        rp.parse(resp.text.splitlines())
    except Exception as exc:
        # robots.txt okunamıyorsa/timeout olduysa temkinli davran: izin verme.
        logger.warning(
            "robots.txt okunamadı (%s): %s — güvenlik gereği erişim reddediliyor.",
            robots_url,
            exc,
        )
        return False
    return rp.can_fetch(user_agent, url)


@dataclass
class FetchResult:
    doc_id: str
    url: str
    local_path: str
    sha256: str
    content_type: str
    fetched_at: str
    status: str  # "downloaded" | "unchanged" | "skipped_robots_disallowed"


class Downloader:
    def __init__(
        self,
        raw_dir: str | Path,
        manifest_path: str | Path | None = None,
        user_agent: str | None = None,
        delay_seconds: float | None = None,
    ):
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = Path(manifest_path or self.raw_dir / "manifest.json")
        self.user_agent = user_agent or os.environ.get(
            "INGEST_USER_AGENT", DEFAULT_USER_AGENT
        )
        self.delay_seconds = float(
            delay_seconds
            if delay_seconds is not None
            else os.environ.get("INGEST_REQUEST_DELAY_SECONDS", DEFAULT_DELAY_SECONDS)
        )
        self.manifest: dict[str, dict] = self._load_manifest()

    def _load_manifest(self) -> dict[str, dict]:
        if self.manifest_path.exists():
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return {}

    def _save_manifest(self) -> None:
        self.manifest_path.write_text(
            json.dumps(self.manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def fetch(self, source: SourceDoc) -> FetchResult:
        if not _robots_allows(source.url, self.user_agent):
            logger.warning(
                "[%s] robots.txt otomatik erişime izin vermiyor: %s",
                source.doc_id,
                source.url,
            )
            return FetchResult(
                doc_id=source.doc_id,
                url=source.url,
                local_path="",
                sha256="",
                content_type="",
                fetched_at=datetime.now(timezone.utc).isoformat(),
                status="skipped_robots_disallowed",
            )

        resp = requests.get(
            source.url,
            headers={"User-Agent": self.user_agent},
            timeout=30,
        )
        resp.raise_for_status()
        content = resp.content
        sha256 = hashlib.sha256(content).hexdigest()

        content_type = resp.headers.get("Content-Type", "")
        ext = _guess_extension(content_type, source.url)
        local_path = self.raw_dir / f"{source.doc_id}{ext}"

        prev = self.manifest.get(source.doc_id)
        status = "downloaded"
        if prev and prev.get("sha256") == sha256:
            status = "unchanged"
            logger.info("[%s] değişiklik yok (hash aynı), atlanıyor.", source.doc_id)
        else:
            local_path.write_bytes(content)
            logger.info("[%s] indirildi -> %s", source.doc_id, local_path)

        result = FetchResult(
            doc_id=source.doc_id,
            url=source.url,
            local_path=str(local_path) if status != "skipped_robots_disallowed" else "",
            sha256=sha256,
            content_type=content_type,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status=status,
        )
        self.manifest[source.doc_id] = asdict(result)
        self._save_manifest()

        time.sleep(self.delay_seconds)
        return result

    def register_manual_file(self, source: SourceDoc, file_path: str | Path) -> FetchResult:
        """
        robots.txt otomatik erişime izin vermediğinde kullanılır: belgeyi siz
        tarayıcınızdan elle indirip bir yere kaydedersiniz, bu fonksiyon o
        dosyayı data/raw/ içine kopyalar, hash'ler ve manifest'e işler —
        tıpkı otomatik indirilmiş gibi ama status="downloaded_manual" ile
        işaretlenir (kaynağın ayırt edilebilmesi için).
        """
        src_path = Path(file_path)
        if not src_path.exists():
            raise FileNotFoundError(f"Dosya bulunamadı: {src_path}")

        content = src_path.read_bytes()
        sha256 = hashlib.sha256(content).hexdigest()
        ext = src_path.suffix or ".bin"
        local_path = self.raw_dir / f"{source.doc_id}{ext}"

        prev = self.manifest.get(source.doc_id)
        status = "downloaded_manual"
        if prev and prev.get("sha256") == sha256:
            status = "unchanged"
        else:
            local_path.write_bytes(content)
            logger.info("[%s] elle indirilen dosya kaydedildi -> %s", source.doc_id, local_path)

        result = FetchResult(
            doc_id=source.doc_id,
            url=source.url,
            local_path=str(local_path),
            sha256=sha256,
            content_type="",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status=status,
        )
        self.manifest[source.doc_id] = asdict(result)
        self._save_manifest()
        return result

    def sync_raw_dir(self, sources: list[SourceDoc]) -> list[FetchResult]:
        """
        data/raw/ klasörünü tarar; her SourceDoc.doc_id için, o isimle başlayan
        bir dosya (herhangi bir uzantıyla, ör. doc_id.pdf, doc_id.docx) bulursa
        hash'ler ve manifest'e kaydeder. Böylece tek tek --register-manual
        çağırmak yerine, dosyaları klasöre elle koyup tek komutla hepsini
        birden kaydedebilirsiniz.
        """
        results: list[FetchResult] = []
        for source in sources:
            matches = [
                p
                for p in self.raw_dir.glob(f"{source.doc_id}.*")
                if p.name != "manifest.json"
            ]
            if not matches:
                logger.info("[%s] data/raw/ içinde dosya bulunamadı, atlanıyor.", source.doc_id)
                continue
            if len(matches) > 1:
                logger.warning(
                    "[%s] birden fazla dosya eşleşti (%s), ilki kullanılıyor.",
                    source.doc_id,
                    [m.name for m in matches],
                )
            result = self.register_manual_file(source, matches[0])
            results.append(result)
        return results