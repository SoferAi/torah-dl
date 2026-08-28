import json
from unittest.mock import Mock

import pytest
import requests

from torah_dl.core.exceptions import ContentExtractionError, DownloadURLError, NetworkError, TitleExtractionError
from torah_dl.core.extractors.chabad import ChabadExtractor

ARTICLE_URL = "https://www.chabad.org/multimedia/audio_cdo/aid/6145227/jewish/The-Mitzvah-to-Be-Travelers.htm"


def _metadata_response(metadata: dict) -> Mock:
    response = Mock()
    response.text = (
        "if (typeof(Co) === 'undefined') Co = {};\n"
        "if (typeof(Co.MediaInfo) === 'undefined') Co.MediaInfo = {};\n"
        f"Co.MediaInfo['item6145227'] = {json.dumps(metadata)};"
    )
    return response


def test_can_handle_chabad_audio_pages():
    extractor = ChabadExtractor()

    assert extractor.can_handle(ARTICLE_URL)
    assert extractor.can_handle("https://es.chabad.org/multimedia/audio_cdo/aid/6145227/jewish/example.htm")
    assert not extractor.can_handle("https://www.chabad.org/multimedia/video_cdo/aid/6145227/jewish/example.htm")
    assert not extractor.can_handle("https://www.chabad.org/library/article_cdo/aid/6145227/jewish/example.htm")


def test_extract_downloadable_audio(monkeypatch: pytest.MonkeyPatch):
    response = _metadata_response({
        "Title": "  The Mitzvah   to Be Travelers ",
        "Media": {"Type": "audio", "AllowDownload": True, "Id": "12505208"},
    })
    request = Mock(return_value=response)
    monkeypatch.setattr("torah_dl.core.extractors.chabad.requests.get", request)

    result = ChabadExtractor().extract(ARTICLE_URL)

    assert result.download_url == (
        "https://embed.chabad.org/multimedia/mediaplayer/flash_media_player_content.xml.asp"
        "?what=load&aid=6145227&iid=12505208"
    )
    assert result.title == "The Mitzvah to Be Travelers"
    assert result.file_format == "audio/mp3"
    assert result.file_name == "12505208.mp3"
    request.assert_called_once_with(
        ChabadExtractor.METADATA_URL,
        params={"what": "json", "aid": "6145227"},
        timeout=30,
        headers={"User-Agent": "torah-dl/1.0"},
    )


@pytest.mark.parametrize(
    "metadata",
    [
        {"Error": "1", "Message": "Content not available"},
        {"Title": "Collection page"},
        {"Title": "Video", "Media": {"Type": "video", "AllowDownload": False, "Id": "123"}},
        {"Title": "Missing ID", "Media": {"Type": "audio", "AllowDownload": True}},
    ],
)
def test_extract_rejects_unavailable_media(monkeypatch: pytest.MonkeyPatch, metadata: dict):
    monkeypatch.setattr(
        "torah_dl.core.extractors.chabad.requests.get",
        Mock(return_value=_metadata_response(metadata)),
    )

    with pytest.raises(DownloadURLError):
        ChabadExtractor().extract(ARTICLE_URL)


def test_extract_requires_title(monkeypatch: pytest.MonkeyPatch):
    metadata = {"Media": {"Type": "audio", "AllowDownload": True, "Id": "12505208"}}
    monkeypatch.setattr(
        "torah_dl.core.extractors.chabad.requests.get",
        Mock(return_value=_metadata_response(metadata)),
    )

    with pytest.raises(TitleExtractionError):
        ChabadExtractor().extract(ARTICLE_URL)


@pytest.mark.parametrize("body", ["not metadata", "Co.MediaInfo.item = {not-json};"])
def test_extract_rejects_malformed_metadata(monkeypatch: pytest.MonkeyPatch, body: str):
    response = Mock(text=body)
    monkeypatch.setattr("torah_dl.core.extractors.chabad.requests.get", Mock(return_value=response))

    with pytest.raises(ContentExtractionError):
        ChabadExtractor().extract(ARTICLE_URL)


def test_extract_wraps_request_errors(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "torah_dl.core.extractors.chabad.requests.get",
        Mock(side_effect=requests.RequestException("connection failed")),
    )

    with pytest.raises(NetworkError):
        ChabadExtractor().extract(ARTICLE_URL)
