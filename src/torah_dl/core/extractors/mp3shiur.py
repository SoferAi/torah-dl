import re
from re import Pattern
from typing import ClassVar

import requests
from bs4 import BeautifulSoup, Tag

from ..exceptions import DownloadURLError, NetworkError
from ..models import Extraction, ExtractionExample, Extractor


class Mp3ShiurExtractor(Extractor):
    """Extract audio content from mp3shiur.com."""

    name: str = "MP3Shiur"
    homepage: str = "http://www.mp3shiur.com"

    EXAMPLES: ClassVar[list[ExtractionExample]] = [
        ExtractionExample(
            name="mp3shiur_example",
            url="http://www.mp3shiur.com/prodDetails.asp?catID=437&prodID=5042",
            download_url="http://download.mp3shiur.com/Kesubos 002  2A L4.mp3",
            title="Kesubos 002 2A L4",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="mp3shiur_example2",
            url="http://www.mp3shiur.com/prodDetails.asp?catID=391&prodID=3557",
            download_url="http://download.mp3shiur.com/03 Mishmar Kedushin 3A Kinyun Moel.mp3",
            title="03 Mishmar Kedushin 3A Kinyun Moel",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="invalid_link",
            url="http://www.mp3shiur.com/prodDetails.asp?catID=437&prodID=0000",
            download_url="",
            title="",
            file_format="",
            valid=False,
        ),
    ]

    URL_PATTERN = re.compile(r"https?://(?:www\.)?mp3shiur\.com/prodDetails\.asp", re.IGNORECASE)

    @property
    def url_patterns(self) -> list[Pattern]:
        return [self.URL_PATTERN]

    def _find_download_link(self, soup: BeautifulSoup) -> Tag:
        # Find the download link (case-insensitive, allow extra params)
        download_link = soup.find("a", href=re.compile(r"download\\.asp\\?fn=", re.IGNORECASE))
        if not isinstance(download_link, Tag):
            # Try a fallback: search all <a> tags for href containing 'download.asp?fn='
            for a in soup.find_all("a", href=True):
                if isinstance(a, Tag):
                    href_val = a.get("href", "")
                    if isinstance(href_val, str) and "download.asp?fn=" in href_val.lower():
                        return a
            raise DownloadURLError()
        return download_link

    def _extract_file_name(self, href: str) -> str:
        import urllib.parse

        qs = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
        file_name = qs.get("fn", [None])[0]
        if not file_name:
            # Fallback: try to extract file name from the href directly
            match = re.search(r"fn=([^&]+)", href)
            if match:
                file_name = match.group(1)
            else:
                raise DownloadURLError()
        return file_name

    def _normalize_title(self, s: str) -> str:
        # Remove .mp3 extension and normalize spaces
        return re.sub(r"\s+", " ", s.replace(".mp3", "")).strip()

    def extract(self, url: str) -> Extraction:
        try:
            response = requests.get(url, timeout=30, headers={"User-Agent": "torah-dl/1.0"})
            response.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(str(e)) from e

        soup = BeautifulSoup(response.content, "html.parser")
        download_link = self._find_download_link(soup)
        href = download_link.get("href")
        if not isinstance(href, str):
            raise DownloadURLError()
        file_name = self._extract_file_name(href)
        download_url = f"http://download.mp3shiur.com/{file_name}"

        # Normalize file name for title comparison
        normalized_file_name = self._normalize_title(file_name)
        title = None
        # Prefer a <b> tag that matches the normalized file name
        for tag in soup.find_all("b"):
            tag_text = tag.text.strip()
            if tag_text and ".mp3" not in tag_text and len(tag_text) > 5:
                normalized_tag_text = self._normalize_title(tag_text)
                if normalized_file_name in normalized_tag_text or normalized_tag_text in normalized_file_name:
                    title = tag_text
                    break
        # Fallback: use normalized file name (no .mp3)
        if not title:
            title = normalized_file_name

        return Extraction(
            download_url=download_url,
            title=title,
            file_format="audio/mp3",
            file_name=file_name,
        )
