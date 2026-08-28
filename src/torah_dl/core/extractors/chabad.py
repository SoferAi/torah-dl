import json
import re
from re import Pattern
from typing import Any, ClassVar

import requests

from ..exceptions import ContentExtractionError, DownloadURLError, NetworkError, TitleExtractionError
from ..models import Extraction, ExtractionExample, Extractor


class ChabadExtractor(Extractor):
    """Extract downloadable audio from individual Chabad.org media pages."""

    name: str = "Chabad.org"
    homepage: str = "https://www.chabad.org"

    EXAMPLES: ClassVar[list[ExtractionExample]] = [
        ExtractionExample(
            name="audio_page",
            url="https://www.chabad.org/multimedia/audio_cdo/aid/6145227/jewish/The-Mitzvah-to-Be-Travelers.htm",
            download_url=(
                "https://embed.chabad.org/multimedia/mediaplayer/flash_media_player_content.xml.asp"
                "?what=load&aid=6145227&iid=12505208"
            ),
            title="The Mitzvah to Be Travelers",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="invalid_audio_page",
            url="https://www.chabad.org/multimedia/audio_cdo/aid/0/jewish/Unavailable.htm",
            download_url="",
            title="",
            file_format="",
            valid=False,
        ),
    ]

    URL_PATTERN = re.compile(
        r"https?://(?:[\w-]+\.)*chabad\.org/multimedia/audio_cdo/aid/(\d+)(?:/|$)",
        re.IGNORECASE,
    )
    METADATA_URL = "https://embed.chabad.org/multimedia/mediaplayer/flash_media_player_content.xml.asp"
    METADATA_PATTERN = re.compile(r"Co\.MediaInfo\[[^]]+\]\s*=\s*(\{.*\})\s*;\s*$", re.DOTALL)

    _ERR_ARTICLE_ID = "Could not extract a Chabad.org article ID"
    _ERR_MEDIA = "Chabad.org page does not contain downloadable media"
    _ERR_NOT_DOWNLOADABLE = "Chabad.org does not offer this media as a downloadable audio file"
    _ERR_MEDIA_ID = "Could not extract the Chabad.org media ID"
    _ERR_TITLE = "Could not extract the Chabad.org media title"
    _ERR_METADATA = "Could not parse Chabad.org media metadata"
    _ERR_INVALID_METADATA = "Chabad.org returned invalid media metadata"

    @property
    def url_patterns(self) -> list[Pattern]:
        return [self.URL_PATTERN]

    def extract(self, url: str) -> Extraction:
        """Extract a stable Chabad.org MP3 download redirect and its title."""
        article_id = self._extract_article_id(url)
        if not article_id:
            raise DownloadURLError(self._ERR_ARTICLE_ID)

        metadata = self._fetch_metadata(article_id)
        if metadata.get("Error"):
            raise DownloadURLError(str(metadata.get("Message", "Content not available")))

        media = metadata.get("Media")
        if not isinstance(media, dict):
            raise DownloadURLError(self._ERR_MEDIA)

        if media.get("Type") != "audio" or media.get("AllowDownload") is not True:
            raise DownloadURLError(self._ERR_NOT_DOWNLOADABLE)

        media_id = str(media.get("Id", "")).strip()
        if not media_id.isdigit():
            raise DownloadURLError(self._ERR_MEDIA_ID)

        title = self._clean_title(metadata.get("Title"))
        if not title:
            raise TitleExtractionError(self._ERR_TITLE)

        download_url = f"{self.METADATA_URL}?what=load&aid={article_id}&iid={media_id}"
        return Extraction(
            download_url=download_url,
            title=title,
            file_format="audio/mp3",
            file_name=f"{media_id}.mp3",
        )

    def _extract_article_id(self, url: str) -> str | None:
        if match := self.URL_PATTERN.match(url):
            return match.group(1)
        return None

    def _fetch_metadata(self, article_id: str) -> dict[str, Any]:
        try:
            response = requests.get(
                self.METADATA_URL,
                params={"what": "json", "aid": article_id},
                timeout=30,
                headers={"User-Agent": "torah-dl/1.0"},
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(str(e)) from e

        match = self.METADATA_PATTERN.search(response.text)
        if not match:
            raise ContentExtractionError(self._ERR_METADATA)

        try:
            metadata = json.loads(match.group(1))
        except json.JSONDecodeError as e:
            raise ContentExtractionError(self._ERR_METADATA) from e

        if not isinstance(metadata, dict):
            raise ContentExtractionError(self._ERR_INVALID_METADATA)
        return metadata

    @staticmethod
    def _clean_title(value: Any) -> str:
        if not isinstance(value, str):
            return ""
        return " ".join(value.split())
