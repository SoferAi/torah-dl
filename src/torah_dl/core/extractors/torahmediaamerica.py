import re
from re import Pattern

import requests
from bs4 import BeautifulSoup

from ..exceptions import DownloadURLError
from ..models import Extraction, ExtractionExample, Extractor


class TorahMediaAmericaExtractor(Extractor):
    """Extract audio content from TorahMediaAmerica.com.

    This extractor handles URLs from torahmediaamerica.com and constructs the MP3 download link
    using the numeric ID in the URL.
    """

    name: str = "TorahMediaAmerica"
    homepage: str = "http://torahmediaamerica.com"

    EXAMPLES = [  # noqa: RUF012
        ExtractionExample(
            name="main_page",
            url="http://torahmediaamerica.com/shiur-1024531.html",
            download_url="https://torahcdn.net/tdn/1024531.mp3",
            title="01 Introduction to Shoftim (Rus) (2013)",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="another_page",
            url="http://torahmediaamerica.com/shiur-1025096.html",
            download_url="https://torahcdn.net/tdn/1025096.mp3",
            title="Covering Hair and Negiya shel Chiba (Ohr Lagolah 5776)",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="invalid_link",
            url="http://torahmediaamerica.com/shiur-foobar.html",
            download_url="",
            title="",
            file_format="",
            valid=False,
        ),
    ]

    # URL pattern for TorahMediaAmerica.com pages
    URL_PATTERN = re.compile(r"https?://(?:www\.)?torahmediaamerica\.com/shiur-([\w-]+)\.html")

    @property
    def url_patterns(self) -> list[Pattern]:
        """Return the URL pattern(s) that this extractor can handle."""
        return [self.URL_PATTERN]

    def can_handle(self, url: str) -> bool:
        match = self.URL_PATTERN.search(url)
        return bool(match)

    def extract(self, url: str) -> Extraction:
        """Extract download URL and title from a TorahMediaAmerica.com page."""
        match = self.URL_PATTERN.search(url)
        if not match:
            raise DownloadURLError()
        shiur_id = match.group(1)
        # Only allow numeric IDs for extraction
        if not shiur_id.isdigit():
            raise DownloadURLError()
        download_url = f"https://torahcdn.net/tdn/{shiur_id}.mp3"
        file_name = f"{shiur_id}.mp3"

        # Fetch the page and extract the title
        try:
            response = requests.get(url, timeout=30, headers={"User-Agent": "torah-dl/1.0"})
            response.raise_for_status()
        except requests.RequestException as e:
            raise DownloadURLError(str(e)) from e

        soup = BeautifulSoup(response.content, "html.parser")
        # Try to extract the title from a heading or title tag
        title = None
        # Try h2, h1, or title tag
        if (h2 := soup.find("h2")) and h2.get_text(strip=True):
            title = h2.get_text(strip=True)
        elif (h1 := soup.find("h1")) and h1.get_text(strip=True):
            title = h1.get_text(strip=True)
        elif (title_tag := soup.find("title")) and title_tag.get_text(strip=True):
            title = title_tag.get_text(strip=True)
        else:
            # Fallback: try to find a div with class 'title' or similar
            if (div_title := soup.find("div", class_="title")) and div_title.get_text(strip=True):
                title = div_title.get_text(strip=True)

        title = "" if not title else title.split(" - ")[0].strip()

        return Extraction(download_url=download_url, title=title, file_format="audio/mp3", file_name=file_name)
