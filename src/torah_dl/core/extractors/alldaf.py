import re
from re import Pattern

import requests
from bs4 import BeautifulSoup

from ..exceptions import DownloadURLError, NetworkError
from ..models import Extraction, ExtractionExample, Extractor


class AllDafExtractor(Extractor):
    """Extract audio/video content from AllDaf.org.

    This extractor handles URLs from alldaf.org and extracts MP3/MP4 download
    links along with their associated titles from various locations in the page.
    """

    EXAMPLES = [  # noqa: RUF012
        ExtractionExample(
            name="main_page",
            url="https://alldaf.org/p/36785",
            download_url="https://media.ou.org/torah/2925/36785/36785.mp3",
            title="Sanhedrin 40",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="another_page",
            url="https://alldaf.org/p/215503",
            download_url="https://media.ou.org/torah/4049/215503/215503.mp3",
            title="Sanhedrin 40 - Cycle 14",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="invalid_link",
            url="https://alldaf.org/p/000000",
            download_url="",
            title="",
            file_format="",
            valid=False,
        ),
    ]

    # URL pattern for AllDaf.org pages
    URL_PATTERN = re.compile(r"https?://(?:www\.)?alldaf\.org/")

    # Patterns to find download URLs in various locations
    ACTION_BAR_URL_PATTERN = re.compile(r"s3Url=(.*?\.mp[34])")
    ACTION_BAR_TITLE_PATTERN = re.compile(r"title=(.*?)&")
    SCRIPT_URL_PATTERN = re.compile(
        r"(?:audioUrl|audio_url|url|videoUrl)\s*:\s*['\"]([^'\"]+\.mp[34])['\"]", flags=re.IGNORECASE
    )
    RAW_URL_PATTERN = re.compile(r"https?://[^\"'\s]+\.mp[34]")

    @property
    def url_patterns(self) -> list[Pattern]:
        """Return the URL pattern(s) that this extractor can handle.

        Returns:
            List[Pattern]: List of compiled regex patterns matching AllDaf.org URLs
        """
        return [self.URL_PATTERN]

    def extract(self, url: str) -> Extraction:
        """Extract download URL and title from an AllDaf.org page.

        Args:
            url: The AllDaf.org URL to extract from

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
        # html = str(response.content)

        # Try finding download link in the action bar first
        action_bar_link = soup.select_one('.publication-action-bar__item[href*="s3Url="]')
        if action_bar_link:
            href = action_bar_link.get("href", "")
            s3_url_match = self.ACTION_BAR_URL_PATTERN.search(href)
            title_match = self.ACTION_BAR_TITLE_PATTERN.search(href)

            if s3_url_match:
                download_url = requests.utils.unquote(s3_url_match.group(1))
                title = requests.utils.unquote(title_match.group(1)) if title_match else None
                file_format = f"audio/{download_url.split('.')[-1].lower()}"
                file_name = download_url.split("/")[-1]
                return Extraction(download_url=download_url, title=title, file_format=file_format, file_name=file_name)

        # # Try finding audio/video elements as fallback
        # media_selector = (
        #     'audio source[src*=".mp3"], audio[src*=".mp3"], a[href*=".mp3"],'
        #     'video source[src*=".mp4"], video[src*=".mp4"], .jw-video[src*=".mp4"]'
        # )
        # media_element = soup.select_one(media_selector)
        # if media_element:
        #     src = media_element.get("src") or media_element.get("href")
        #     if src:
        #         title = soup.select_one("h1")
        #         title = title.get_text().strip() if title else None
        #         file_format = f"audio/{src.split('.')[-1].lower()}"
        #         file_name = src.split("/")[-1]
        #         return Extraction(download_url=src, title=title, file_format=file_format, file_name=file_name)

        # Try finding audio/video URL in script tags
        # for script in soup.find_all("script"):
        #     content = script.string or ""
        #     media_url_match = self.SCRIPT_URL_PATTERN.search(content)
        #     if media_url_match:
        #         download_url = media_url_match.group(1)
        #         title = soup.select_one("h1")
        #         title = title.get_text().strip() if title else None
        #         file_format = f"audio/{download_url.split('.')[-1].lower()}"
        #         file_name = download_url.split("/")[-1]
        #         return Extraction(download_url=download_url, title=title, file_format=file_format, file_name=file_name)

        # Try finding in the raw HTML for any mp3/mp4 URLs
        # media_url_match = self.RAW_URL_PATTERN.search(html)
        # if media_url_match:
        #     download_url = media_url_match.group(0)
        #     title = soup.select_one("h1")
        #     title = title.get_text().strip() if title else None
        #     file_format = f"audio/{download_url.split('.')[-1].lower()}"
        #     file_name = download_url.split("/")[-1]
        #     return Extraction(download_url=download_url, title=title, file_format=file_format, file_name=file_name)

        raise DownloadURLError()
