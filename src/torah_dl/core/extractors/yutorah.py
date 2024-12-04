import re
from re import Pattern

import requests
from bs4 import BeautifulSoup

from ..exceptions import ContentExtractionError, DownloadURLError, NetworkError, TitleExtractionError
from ..models import Extraction, Extractor


class YutorahExtractor(Extractor):
    """Extract audio content from YUTorah.org.

    This extractor handles URLs from www.yutorah.org and extracts MP3 download
    links along with their associated titles from the page's JavaScript content.
    """

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
            raise NetworkError(str(e)) from e

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

        return Extraction(download_url=download_url, title=title, file_format="mp3", file_name=file_name)
