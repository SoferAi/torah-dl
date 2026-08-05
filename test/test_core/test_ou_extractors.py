from __future__ import annotations

import pytest
import requests
from bs4 import BeautifulSoup

from torah_dl.core.extractors._ou import extract_structured_media
from torah_dl.core.extractors.alldaf import AllDafExtractor
from torah_dl.core.extractors.outorah import OutorahExtractor
from torah_dl.core.models import Extractor


class _MockResponse:
    def __init__(self, html: str):
        self.content = html.encode()

    def raise_for_status(self) -> None:
        pass


@pytest.mark.parametrize(
    ("extractor", "url", "title", "download_url"),
    [
        (
            OutorahExtractor(),
            "https://outorah.org/p/212365/",
            "Parshat Miketz: A Chanukah Charade",
            "https://media.ou.org/torah/4093/212365/212365.mp3",
        ),
        (
            AllDafExtractor(),
            "https://alldaf.org/p/36785",
            "Sanhedrin 40",
            "https://media.ou.org/torah/2925/36785/36785.mp3",
        ),
    ],
)
def test_extracts_media_from_current_nuxt_payload(
    monkeypatch: pytest.MonkeyPatch,
    extractor: Extractor,
    url: str,
    title: str,
    download_url: str,
) -> None:
    post_id = download_url.rsplit("/", maxsplit=1)[-1].removesuffix(".mp3")
    escaped_download_url = download_url.replace("/", r"\u002F")
    html = f"""
        <html>
          <head>
            <script type="application/ld+json">
              {{"@context":"https://schema.org/","@type":"AudioObject","name":"{title}"}}
            </script>
          </head>
          <body>
            <script id="__NUXT_DATA__" type="application/json">
              ["https:\\u002F\\u002Fmedia.ou.org\\u002Ftorah\\u002F9999\\u002F111\\u002F111.mp3",
               "{escaped_download_url}", "{post_id}"]
            </script>
          </body>
        </html>
    """

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: _MockResponse(html))

    extraction = extractor.extract(url)

    assert extraction.download_url == download_url
    assert extraction.title == title
    assert extraction.file_format == "audio/mp3"
    assert extraction.file_name == f"{post_id}.mp3"


@pytest.mark.parametrize(
    ("extractor", "url", "link_class"),
    [
        (OutorahExtractor(), "https://outorah.org/p/123", ""),
        (AllDafExtractor(), "https://alldaf.org/p/123", "publication-action-bar__item"),
    ],
)
def test_preserves_legacy_download_link_fallback(
    monkeypatch: pytest.MonkeyPatch,
    extractor: Extractor,
    url: str,
    link_class: str,
) -> None:
    html = f"""
        <a class="{link_class}"
           href="https://outorah.org/download?title=Legacy%20Title&amp;s3Url=https://media.ou.org/torah/1/123/123.mp3">
          Download
        </a>
    """
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: _MockResponse(html))

    extraction = extractor.extract(url)

    assert extraction.download_url == "https://media.ou.org/torah/1/123/123.mp3"
    assert extraction.title == "Legacy Title"
    assert extraction.file_format == "audio/mp3"


def test_extracts_video_from_nested_json_ld_after_malformed_script() -> None:
    html = r"""
        <script type="application/ld+json">not-json</script>
        <script type="application/ld+json">
          {
            "@graph": [
              {"@type": 123, "name": "Not media"},
              {"@type": ["Thing", "VideoObject"], "name": "  Sample Video  "}
            ]
          }
        </script>
        <script>
          ["https:\u002F\u002Fmedia.ou.org\u002Ftorah\u002F42\u002F987\u002F987.mp4"]
        </script>
    """

    extraction = extract_structured_media(
        "https://outorah.org/p/987",
        html,
        BeautifulSoup(html, "html.parser"),
    )

    assert extraction is not None
    assert extraction.download_url == "https://media.ou.org/torah/42/987/987.mp4"
    assert extraction.title == "Sample Video"
    assert extraction.file_format == "video/mp4"
    assert extraction.file_name == "987.mp4"


@pytest.mark.parametrize(
    ("url", "html"),
    [
        ("https://outorah.org/series/4093", ""),
        (
            "https://outorah.org/p/123",
            '<script type="application/ld+json">{"@type":"AudioObject","name":"Missing media"}</script>',
        ),
        (
            "https://outorah.org/p/123",
            r'<script>["https:\u002F\u002Fmedia.ou.org\u002Ftorah\u002F1\u002F123\u002F123.mp3"]</script>',
        ),
    ],
)
def test_structured_media_requires_post_id_media_url_and_title(url: str, html: str) -> None:
    assert extract_structured_media(url, html, BeautifulSoup(html, "html.parser")) is None
