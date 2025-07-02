import re
from re import Pattern
from urllib.parse import parse_qs, urlparse

import requests

from ..exceptions import ContentExtractionError, DownloadURLError, NetworkError, TitleExtractionError
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

    def __init__(self):
        """Initialize the Orayta extractor."""
        from .yutorah import YutorahExtractor

        self.yutorah_extractor = YutorahExtractor()

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
        try:
            # Extract shiur information from the URL
            shiur_id, shiur_title = self._extract_shiur_info(url)

            # Try to construct the YUTorah URL and extract from it
            yutorah_url = self._construct_yutorah_url(shiur_id, shiur_title)

            try:
                # Use the YUTorah extractor to get the actual download URL and title
                extraction = self.yutorah_extractor.extract(yutorah_url)
            except (DownloadURLError, TitleExtractionError, NetworkError):
                # If YUTorah extraction fails, try to construct the download URL directly
                download_url = self._construct_download_url(shiur_id, shiur_title)

                # Verify the download URL exists
                try:
                    response = requests.head(download_url, timeout=10, headers={"User-Agent": "torah-dl/1.0"})
                    if response.status_code != 200:
                        raise DownloadURLError()
                except requests.RequestException as e:
                    raise DownloadURLError() from e

                file_name = f"{shiur_title.lower().replace(' ', '-')}.mp3"

                return Extraction(
                    download_url=download_url, title=shiur_title, file_format="audio/mp3", file_name=file_name
                )
            else:
                return extraction
        except ContentExtractionError:
            raise
        except Exception as e:
            raise ContentExtractionError() from e

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

    def _construct_yutorah_url(self, shiur_id: str, shiur_title: str) -> str:
        """Construct the corresponding YUTorah.org URL.

        Args:
            shiur_id: The shiur ID
            shiur_title: The shiur title

        Returns:
            str: The YUTorah.org URL
        """
        # Convert title to URL-friendly format (lowercase, replace spaces with hyphens)
        title_slug = shiur_title.lower().replace(" ", "-")
        return f"https://www.yutorah.org/lectures/{shiur_id}/{title_slug}"

    def _construct_download_url(self, shiur_id: str, shiur_title: str) -> str:
        """Construct the direct download URL by scraping the YUTorah page only."""
        # Try to get the actual year and category ID from YUTorah only
        yutorah_url = self._construct_yutorah_url(shiur_id, shiur_title)
        try:
            response = requests.get(yutorah_url, timeout=10, headers={"User-Agent": "torah-dl/1.0"})
            if response.status_code == 200:
                import re

                download_pattern = re.compile(r'"downloadURL":"(https?://[^"]+\.mp3)"')
                match = download_pattern.search(response.text)
                if match:
                    return match.group(1)
        except requests.RequestException:
            pass
        raise DownloadURLError()
