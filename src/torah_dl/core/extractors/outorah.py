import re
import urllib.parse
from re import Pattern

import requests
from bs4 import BeautifulSoup

from ..exceptions import ContentExtractionError, DownloadURLError, NetworkError
from ..models import Extraction, ExtractionExample, Extractor


class OutorahExtractor(Extractor):
    """Extract audio content from Outorah.org.

    This extractor handles URLs from www.outorah.org and extracts MP3 download
    links along with their associated titles from the page's JavaScript content.
    """

    name: str = "OU Torah"
    homepage: str = "https://outorah.org"

    EXAMPLES = [  # noqa: RUF012
        ExtractionExample(
            name="main_page",
            url="https://outorah.org/p/212365",
            download_url="https://media.ou.org/torah/4093/212365/212365.mp3",
            title="Parshat Miketz: A Chanukah Charade",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="invalid_link",
            url="https://outorah.org/p/0000000",
            download_url="",
            title="",
            file_format="",
            valid=False,
        ),
    ]

    # URL pattern for Outorah.org pages
    URL_PATTERN = re.compile(r"https?://(?:www\.)?outorah\.org/")

    # Pattern to find download URL in script tags
    MP3_DOWNLOAD_URL_PATTERN = re.compile(r"s3Url=.*\.mp3")
    MP4_DOWNLOAD_URL_PATTERN = re.compile(r"s3Url=.*\.mp4")

    @property
    def url_patterns(self) -> list[Pattern]:
        """Return the URL pattern(s) that this extractor can handle.

        Returns:
            List[Pattern]: List of compiled regex patterns matching Outorah.org URLs
        """
        return [self.URL_PATTERN]

    def extract(self, url: str) -> Extraction:
        """Extract download URL and title from a Outorah.org page.

        Args:
            url: The Outorah.org URL to extract from

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
        if download_link := soup.find("a", attrs={"href": self.MP3_DOWNLOAD_URL_PATTERN}):
            download_url = re.search(r"s3Url=(.*\.mp3)", download_link["href"]).group(1)
            title = re.search(r"title=(.*?)&", download_link["href"])
            if title:
                title = urllib.parse.unquote(title.group(1))
        elif download_link := soup.find("a", attrs={"href": self.MP4_DOWNLOAD_URL_PATTERN}):
            download_url = re.search(r"s3Url=(.*\.mp4)", download_link["href"]).group(1)
            title = re.search(r"title=(.*?)&", download_link["href"])
            if title:
                title = urllib.parse.unquote(title.group(1))
        else:
            raise DownloadURLError()

        file_name = download_url.split("/")[-1]

        if not download_url or not title:
            raise ContentExtractionError()

        return Extraction(download_url=download_url, title=title, file_format="audio/mp3", file_name=file_name)
