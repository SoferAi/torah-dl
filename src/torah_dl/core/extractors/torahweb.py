import re
from re import Pattern
from typing import ClassVar

import requests
from bs4 import BeautifulSoup, Tag

from ..exceptions import DownloadURLError, NetworkError
from ..models import Extraction, ExtractionExample, Extractor


class TorahWebExtractor(Extractor):
    """Extract audio content from TorahWeb.org shiur pages."""

    name: str = "TorahWeb"
    homepage: str = "https://www.torahweb.org"

    EXAMPLES: ClassVar[list[ExtractionExample]] = [
        ExtractionExample(
            name="torahweb_example",
            url="https://www.torahweb.org/audio/rlop_062820.html",
            download_url="https://www.torahweb.org/torah/audio/2020/coronavirus/rlop_062820.mp3",
            title="A Positive Paradigm Shift Brought by COVID-19 (2020)",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="torahweb_example2",
            url="https://torahweb.org/audio/rsch_091811.html",
            download_url="https://www.torahweb.org/torah/audio/2011/teshuva/rsch_091811.mp3",
            title="Teshuva: Serving Hashem HIS Way, Not Mine (2011)",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="invalid_link",
            url="https://www.torahweb.org/audio/invalid.html",
            download_url="",
            title="",
            file_format="",
            valid=False,
        ),
    ]

    URL_PATTERN = re.compile(r"https?://(?:www\.)?torahweb\.org/audio/[^/]+\.html")

    @property
    def url_patterns(self) -> list[Pattern]:
        return [self.URL_PATTERN]

    def can_handle(self, url: str) -> bool:
        patterns = self.url_patterns
        if isinstance(patterns, Pattern):
            patterns = [patterns]
        return any(pattern.match(url) for pattern in patterns)

    def extract(self, url: str) -> Extraction:
        try:
            response = requests.get(url, timeout=30, headers={"User-Agent": "torah-dl/1.0"})
            response.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(str(e)) from e

        soup = BeautifulSoup(response.content, "html.parser")
        mp3_link = self._extract_mp3_link(soup)
        if not mp3_link:
            raise DownloadURLError()
        title = self._extract_title(soup)
        file_name = mp3_link.split("/")[-1]
        return Extraction(download_url=mp3_link, title=title, file_format="audio/mp3", file_name=file_name)

    def _extract_mp3_link(self, soup: BeautifulSoup) -> str | None:
        for a in soup.find_all("a", href=True):
            if not isinstance(a, Tag):
                continue
            href = a.get("href")
            if not isinstance(href, str):
                continue
            if href.endswith(".mp3") and href.startswith("/torah/audio/"):
                return "https://www.torahweb.org" + href
            if href.startswith("https://www.torahweb.org/torah/audio/") and href.endswith(".mp3"):
                return href
        # fallback: look for any .mp3 link in the page
        for a in soup.find_all("a", href=True):
            if not isinstance(a, Tag):
                continue
            href = a.get("href")
            if not isinstance(href, str):
                continue
            if ".mp3" in href:
                return href if href.startswith("http") else "https://www.torahweb.org" + href
        return None

    def _extract_title(self, soup: BeautifulSoup) -> str | None:
        h1 = soup.find("h1")
        if h1 and isinstance(h1, Tag):
            small = h1.find("small")
            if small and isinstance(small, Tag):
                # Find the text node immediately after <small>
                found_small = False
                for child in h1.children:
                    if found_small and isinstance(child, str):
                        title = child.strip()
                        if title:
                            return title
                    if child == small:
                        found_small = True
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)
        return None
