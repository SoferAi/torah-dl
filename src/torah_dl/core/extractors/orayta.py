import re
from re import Pattern
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from ..exceptions import ContentExtractionError, DownloadURLError, NetworkError
from ..models import Extraction, ExtractionExample, Extractor


class OraytaExtractor(Extractor):
    """Extract audio content from Orayta.org.

    This extractor handles URLs from www.orayta.org and extracts MP3 download
    links from the corresponding YUTorah.org download URLs.
    """

    name: str = "Orayta"
    homepage: str = "https://orayta.org"

    EXAMPLES = [  # noqa: RUF012
        ExtractionExample(
            name="main_page_2025",
            url="https://www.orayta.org/orayta-torah/audio-shiurim.html?page=lecture&shiurID=1135538&teacherFullName=Rabbi-Binny-Freedman&shiurTitle=Parashat-Emor-the-Blasphemer",
            download_url="https://download.yutorah.org/2025/79131/1135538/parashat-emor-the-blasphemer.mp3",
            title="Parashat Emor: the Blasphemer",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="main_page_2018",
            url="https://www.orayta.org/orayta-torah/audio-shiurim.html?page=lecture&shiurID=909367&teacherFullName=Rabbi-Yitzchak-Blau&shiurTitle=Reuven-Yehudah-and-the-Quest-for-Leadership",
            download_url="https://download.yutorah.org/2018/30423/909367/reuven-yehudah-and-the-quest-for-leadership.mp3",
            title="Reuven, Yehudah, and the Quest for Leadership",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="invalid_link",
            url="https://www.orayta.org/orayta-torah/audio-shiurim.html?page=lecture&shiurID=0000000&teacherFullName=Test&shiurTitle=Test",
            download_url="",
            title="",
            file_format="",
            valid=False,
        ),
    ]

    # URL pattern for Orayta.org pages
    URL_PATTERN = re.compile(r"https?://(?:www\.)?orayta\.org/")

    @property
    def url_patterns(self) -> list[Pattern]:
        """Return the URL pattern(s) that this extractor can handle.

        Returns:
            List[Pattern]: List of compiled regex patterns matching Orayta.org URLs
        """
        return [self.URL_PATTERN]

    def extract(self, url: str) -> Extraction:
        """Extract download URL and title from an Orayta.org page.

        Args:
            url: The Orayta.org URL to extract from

        Returns:
            Extraction: Object containing the download URL and title

        Raises:
            ValueError: If the URL is invalid or content cannot be extracted
            requests.RequestException: If there are network-related issues
        """
        shiur_id, shiur_title = self._extract_shiur_info(url)
        yutorah_url = self._construct_classic_yutorah_url(shiur_id, shiur_title)

        try:
            response = requests.get(yutorah_url, timeout=30, headers={"User-Agent": "torah-dl/1.0"})
            response.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(str(e)) from e  # pragma: no cover

        # classic.yutorah pages still expose the direct mp3 URL in html
        mp3_match = re.search(r"https?://[^\"'\s>]+\.mp3(?:\?[^\"'\s<]*)?", response.text, re.IGNORECASE)
        if not mp3_match:
            raise DownloadURLError()

        download_url = mp3_match.group(0)
        file_name = download_url.split("/")[-1].split("?")[0]
        title = self._extract_title(response.text, shiur_title)
        if not title:
            raise ContentExtractionError()

        return Extraction(download_url=download_url, title=title, file_format="audio/mp3", file_name=file_name)

    def _extract_shiur_info(self, url: str) -> tuple[str, str]:
        """Extract shiurID and shiurTitle from the Orayta URL.

        Args:
            url: The Orayta.org URL to parse

        Returns:
            tuple[str, str]: (shiurID, shiurTitle)

        Raises:
            ContentExtractionError: If required parameters are missing
        """
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        shiur_id = query_params.get("shiurID", [None])[0]
        shiur_title = query_params.get("shiurTitle", [None])[0]

        if not shiur_id or not shiur_title:
            raise ContentExtractionError()

        return shiur_id, shiur_title

    def _construct_classic_yutorah_url(self, shiur_id: str, shiur_title: str) -> str:
        """Construct the classic YUTorah iframe URL.

        Args:
            shiur_id: The shiur ID
            shiur_title: The shiur title

        Returns:
            str: The classic YUTorah URL
        """
        title_slug = shiur_title.lower().replace(" ", "-")
        return f"https://classic.yutorah.org/lectures/lecture_iframe.cfm/{shiur_id}/{title_slug}"

    def _extract_title(self, html: str, fallback_title: str) -> str:
        """Extract title from the classic YUTorah page title."""
        soup = BeautifulSoup(html, "html.parser")
        page_title = soup.title.get_text(strip=True) if soup.title else ""

        # Example: "YUTorah Online - Reuven, Yehudah, and the Quest for Leadership (Rabbi Yitzchak Blau)"
        if page_title.startswith("YUTorah Online - "):
            title = page_title.replace("YUTorah Online - ", "", 1)
            title = re.sub(r"\s+\(Rabbi.*\)$", "", title).strip()
            if title:
                return title

        # Fallback to the Orayta URL slug if title parsing changes upstream
        return fallback_title.replace("-", " ").strip()
