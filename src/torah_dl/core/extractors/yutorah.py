import re
from re import Pattern

import requests
from bs4 import BeautifulSoup

from ..exceptions import ContentExtractionError, DownloadURLError, NetworkError, TitleExtractionError
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

    # Pattern to find download URL in script tags
    DOWNLOAD_URL_PATTERN = re.compile(r'"downloadURL":"(https?://[^\"]+\.mp3)"')

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
        try:
            response = requests.get(url, timeout=30, headers={"User-Agent": "torah-dl/1.0"})
            response.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(str(e)) from e  # pragma: no cover

        # Parse the page content
        soup = BeautifulSoup(response.content, "html.parser")
        script_tag = soup.find("script", string=self.DOWNLOAD_URL_PATTERN)

        if not script_tag:
            raise DownloadURLError()

        # Extract download URL
        match = self.DOWNLOAD_URL_PATTERN.search(str(script_tag))
        if not match:
            raise DownloadURLError()

        download_url = match.group(1)

        file_name = download_url.split("/")[-1]

        # Extract and decode title
        try:
            title_tag = soup.find("h2", itemprop="name")
            title = title_tag.text if title_tag else None

        except (UnicodeError, IndexError) as e:
            raise TitleExtractionError(str(e)) from e

        if not download_url or not title:
            raise ContentExtractionError()

        return Extraction(download_url=download_url, title=title, file_format="audio/mp3", file_name=file_name)
