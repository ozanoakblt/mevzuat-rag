import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.downloader import Downloader
from src.ingestion.sources import SourceDoc

SOURCE = SourceDoc(
    doc_id="test-doc",
    title="Test Belge",
    url="https://example.com/test.pdf",
    fetch_type="direct_file",
    doc_type="kanun",
)


def _mock_response(content: bytes, content_type: str = "application/pdf"):
    resp = MagicMock()
    resp.content = content
    resp.headers = {"Content-Type": content_type}
    resp.raise_for_status = MagicMock()
    return resp


@patch("src.ingestion.downloader._robots_allows", return_value=True)
@patch("src.ingestion.downloader.requests.get")
def test_first_download(mock_get, mock_robots, tmp_path):
    mock_get.return_value = _mock_response(b"%PDF-1.4 fake content")
    d = Downloader(raw_dir=tmp_path, delay_seconds=0)

    result = d.fetch(SOURCE)

    assert result.status == "downloaded"
    assert Path(result.local_path).exists()
    assert Path(result.local_path).read_bytes() == b"%PDF-1.4 fake content"
    assert "test-doc" in d.manifest


@patch("src.ingestion.downloader._robots_allows", return_value=True)
@patch("src.ingestion.downloader.requests.get")
def test_unchanged_hash_skips_rewrite(mock_get, mock_robots, tmp_path):
    mock_get.return_value = _mock_response(b"same content")
    d = Downloader(raw_dir=tmp_path, delay_seconds=0)

    first = d.fetch(SOURCE)
    second = d.fetch(SOURCE)

    assert first.status == "downloaded"
    assert second.status == "unchanged"
    assert first.sha256 == second.sha256


@patch("src.ingestion.downloader._robots_allows", return_value=False)
@patch("src.ingestion.downloader.requests.get")
def test_robots_disallowed_blocks_download(mock_get, mock_robots, tmp_path):
    d = Downloader(raw_dir=tmp_path, delay_seconds=0)

    result = d.fetch(SOURCE)

    assert result.status == "skipped_robots_disallowed"
    assert result.local_path == ""
    mock_get.assert_not_called()


@patch("src.ingestion.downloader._robots_allows", return_value=True)
@patch("src.ingestion.downloader.requests.get")
def test_changed_hash_creates_new_version_entry(mock_get, mock_robots, tmp_path):
    d = Downloader(raw_dir=tmp_path, delay_seconds=0)

    mock_get.return_value = _mock_response(b"v1 content")
    first = d.fetch(SOURCE)

    mock_get.return_value = _mock_response(b"v2 content, changed")
    second = d.fetch(SOURCE)

    assert first.sha256 != second.sha256
    assert second.status == "downloaded"
    assert Path(second.local_path).read_bytes() == b"v2 content, changed"


def test_register_manual_file(tmp_path):
    d = Downloader(raw_dir=tmp_path / "raw", delay_seconds=0)

    manual_source = tmp_path / "manually_downloaded.pdf"
    manual_source.write_bytes(b"%PDF-1.4 manually downloaded content")

    result = d.register_manual_file(SOURCE, manual_source)

    assert result.status == "downloaded_manual"
    assert Path(result.local_path).exists()
    assert Path(result.local_path).read_bytes() == b"%PDF-1.4 manually downloaded content"
    assert d.manifest["test-doc"]["status"] == "downloaded_manual"
