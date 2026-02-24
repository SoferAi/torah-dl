import re
from re import Pattern
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from ..exceptions import ContentExtractionError, DownloadURLError, NetworkError
from ..models import Extraction, ExtractionExample, Extractor


class YutorahExtractor(Extractor):
    """Extract audio content from YUTorah.org.

    This extractor handles URLs from www.yutorah.org and extracts MP3 download
    links along with their associated titles from the page's JavaScript content.
    """

    name: str = "YUTorah"
    homepage: str = "https://yutorah.org"

    EXAMPLES = [  # noqa: RUF012
        ExtractionExample(
            name="main_page",
            url="https://www.yutorah.org/lectures/1116616/Praying-for-Rain-and-the-International-Traveler",
            download_url="https://download.yutorah.org/2024/986/1116616/praying-for-rain-and-the-international-traveler.mp3",
            title="Praying for Rain and the International Traveler",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="short_link",
            url="https://www.yutorah.org/lectures/1117459/",
            download_url="https://download.yutorah.org/2024/986/1117459/davening-with-strep-throat.mp3",
            title="Davening with Strep Throat",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="shiurid_link",
            url="https://www.yutorah.org/lectures/details?shiurid=1117409",
            download_url="https://download.yutorah.org/2024/21197/1117409/ketubot-42-dechitat-aveilut-1.mp3",
            title="Ketubot 42: Dechitat Aveilut (1)",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="invalid_link",
            url="https://www.yutorah.org/lectures/details?shiurid=0000000",
            download_url="",
            title="",
            file_format="",
            valid=False,
        ),
    ]

    # URL pattern for YUTorah.org pages
    URL_PATTERN = re.compile(r"https?://(?:www\.)?yutorah\.org/")

    DOWNLOAD_URL_PATTERN = re.compile(r"https?://[^\"'\s>]+\.mp3(?:\?[^\"'\s<]*)?", re.IGNORECASE)
    SHIUR_ID_PATTERN = re.compile(r"/(?:lectures|sidebar/lecturedata)/(?:details\?shiurid=)?(\d+)")

    @property
    def url_patterns(self) -> list[Pattern]:
        """Return the URL pattern(s) that this extractor can handle.

        Returns:
            List[Pattern]: List of compiled regex patterns matching YUTorah.org URLs
        """
        return [self.URL_PATTERN]

    def extract(self, url: str) -> Extraction:
        """Extract download URL and title from a YUTorah.org page.

        Args:
            url: The YUTorah.org URL to extract from

        Returns:
            Extraction: Object containing the download URL and title

        Raises:
            ValueError: If the URL is invalid or content cannot be extracted
            requests.RequestException: If there are network-related issues
        """
        shiur_id = self._extract_shiur_id(url)
        if not shiur_id:
            raise ContentExtractionError()

        classic_url = f"https://classic.yutorah.org/lectures/lecture_iframe.cfm/{shiur_id}"
        try:
            response = requests.get(classic_url, timeout=30, headers={"User-Agent": "torah-dl/1.0"})
            response.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(str(e)) from e  # pragma: no cover

        if not (match := self.DOWNLOAD_URL_PATTERN.search(response.text)):
            raise DownloadURLError()

        download_url = match.group(0).replace("-.mp3", ".mp3")
        file_name = download_url.split("/")[-1].split("?")[0]
        title = self._extract_title(response.text)
        if not title:
            raise ContentExtractionError()

        return Extraction(download_url=download_url, title=title, file_format="audio/mp3", file_name=file_name)

    def _extract_shiur_id(self, url: str) -> str | None:
        query = parse_qs(urlparse(url).query)
        if shiurid := query.get("shiurid", [None])[0]:
            return shiurid
        if match := re.search(r"/lectures/(\d+)", url):
            return match.group(1)
        if match := re.search(r"/sidebar/lecturedata/(\d+)", url):
            return match.group(1)
        if match := self.SHIUR_ID_PATTERN.search(url):
            return match.group(1)
        return None

    def _extract_title(self, html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        page_title = soup.title.get_text(strip=True) if soup.title else ""
        if page_title.startswith("YUTorah Online - "):
            title = page_title.replace("YUTorah Online - ", "", 1)
            title = re.sub(r"\s+\(Rabbi.*\)$", "", title).strip()
            return title or None
        return None
