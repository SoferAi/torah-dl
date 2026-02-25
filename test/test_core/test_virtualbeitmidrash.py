from __future__ import annotations

import requests

from torah_dl.core.extractors.virtualbeitmidrash import VirtualBeitMidrashExtractor


class _MockResponse:
    def __init__(self, html: str, status_code: int = 200):
        self._html = html
        self.status_code = status_code
        self.content = html.encode("utf-8")
        self.text = html
        self.url = "https://etzion.org.il/en/test"

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)


def test_extract_prefers_youtube_over_mp3(monkeypatch):
    html = """
    <html>
      <head><meta property="og:title" content="Test Video Title | VBM"></head>
      <body>
        <a href="https://example.com/audio.mp3">audio</a>
        <iframe src="https://www.youtube.com/embed/abc123xyz?wmode=opaque"></iframe>
      </body>
    </html>
    """

    def _mock_get(*args, **kwargs):
        return _MockResponse(html)

    monkeypatch.setattr(requests, "get", _mock_get)

    extractor = VirtualBeitMidrashExtractor()
    extraction = extractor.extract("https://etzion.org.il/en/custom/video")
    assert extraction.download_url == "https://www.youtube.com/embed/abc123xyz?wmode=opaque"
    assert extraction.file_format == "video/youtube"
    assert extraction.title == "Test Video Title"


def test_extract_audio_from_audio_tag(monkeypatch):
    html = """
    <html>
      <head><title>Audio Title | VBM</title></head>
      <body>
        <audio src="https://cdn.example.org/lesson-1.mp3"></audio>
      </body>
    </html>
    """

    def _mock_get(*args, **kwargs):
        return _MockResponse(html)

    monkeypatch.setattr(requests, "get", _mock_get)

    extractor = VirtualBeitMidrashExtractor()
    extraction = extractor.extract("https://etzion.org.il/en/custom/audio")
    assert extraction.download_url == "https://cdn.example.org/lesson-1.mp3"
    assert extraction.file_format == "audio/mp3"
    assert extraction.title == "Audio Title"
    assert extraction.file_name == "lesson-1.mp3"


def test_extract_audio_from_raw_html_mp3(monkeypatch):
    html = """
    <html>
      <head><meta property="og:title" content="Raw Html Audio"></head>
      <body>
        <script>const source = "https://media.example.net/path/raw-track.mp3";</script>
      </body>
    </html>
    """

    def _mock_get(*args, **kwargs):
        return _MockResponse(html)

    monkeypatch.setattr(requests, "get", _mock_get)

    extractor = VirtualBeitMidrashExtractor()
    extraction = extractor.extract("https://etzion.org.il/en/custom/raw-audio")
    assert extraction.download_url == "https://media.example.net/path/raw-track.mp3"
    assert extraction.file_format == "audio/mp3"
    assert extraction.title == "Raw Html Audio"
    assert extraction.file_name == "raw-track.mp3"
