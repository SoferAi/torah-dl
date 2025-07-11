import re
from re import Pattern
from typing import ClassVar

import requests
from bs4 import BeautifulSoup, Tag

from ..exceptions import DownloadURLError, NetworkError
from ..models import Extraction, ExtractionExample, Extractor


class NishmatExtractor(Extractor):
    """Extract audio content from Nishmat.net lesson pages.

    This extractor handles URLs from nishmat.net/lesson/ and extracts the direct MP3 download link.
    """

    name: str = "Nishmat"
    homepage: str = "https://nishmat.net"

    EXAMPLES: ClassVar[list[ExtractionExample]] = [
        ExtractionExample(
            name="nishmat_example1",
            url="https://nishmat.net/lesson/the-journey-to-emunah/",
            download_url="https://nishmat.net/wp-content/themes/nishmat/classes/download.php?filename=http://www.nishmattorah.com/uploads/DafnaSeigleman-cr.mp3",
            title="From Egypt to Yam Suf: The Journey to Emunah",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="nishmat_example2",
            url="https://nishmat.net/lesson/16/",
            download_url="https://nishmat.net/wp-content/themes/nishmat/classes/download.php?filename=lecture14.mp3",
            title="Mishloach Manot and Seudat Purim",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="invalid_link",
            url="https://nishmat.net/lesson/nonexistent-lesson/",
            download_url="",
            title="",
            file_format="",
            valid=False,
        ),
    ]

    URL_PATTERN = re.compile(r"https?://(?:www\.)?nishmat\.net/lesson/", re.IGNORECASE)

    @property
    def url_patterns(self) -> list[Pattern]:
        return [self.URL_PATTERN]

    def extract(self, url: str) -> Extraction:
        try:
            response = requests.get(url, timeout=30, headers={"User-Agent": "torah-dl/1.0"})
            response.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(str(e)) from e

        soup = BeautifulSoup(response.content, "html.parser")
        download_link = self._find_download_link(soup)
        if not isinstance(download_link, str) or not download_link:
            raise DownloadURLError()
        title = self._extract_title(soup, download_link)
        file_name = download_link.split("/")[-1]
        file_format = "audio/mp3"
        return Extraction(
            download_url=str(download_link),
            title=title,
            file_format=file_format,
            file_name=file_name,
        )

    def _find_download_link(self, soup) -> str | None:
        # Find the download link (look for a link to download.php with .mp3 in the query, case-insensitive)
        for a in soup.find_all("a", href=True):
            if not isinstance(a, Tag):
                continue
            href = a.get("href")
            if not isinstance(href, str):
                continue
            href_lower = href.lower()
            if (
                "download.php?filename=" in href_lower
                and href_lower.endswith(".mp3")
                and "nishmat.net/wp-content/themes/nishmat/classes/download.php" in href_lower
            ):
                return href
        # fallback: look for any .mp3 link with download.php (case-insensitive)
        for a in soup.find_all("a", href=True):
            if not isinstance(a, Tag):
                continue
            href = a.get("href")
            if not isinstance(href, str):
                continue
            href_lower = href.lower()
            if "download.php?filename=" in href_lower and href_lower.endswith(".mp3"):
                return href
        return None

    def _extract_title(self, soup, download_link: str) -> str:
        post_title_div = soup.find("div", class_="PostTitle")
        if post_title_div:
            title = post_title_div.get_text(strip=True)
        elif h1 := soup.find("h1"):
            title = h1.get_text(strip=True)
        elif title_tag := soup.find("title"):
            title = title_tag.get_text(strip=True)
        else:
            title = download_link.split("/")[-1]
        # Normalize whitespace in title
        if title:
            title = re.sub(r"\s+", " ", title)
        return title
