import re
from re import Pattern

import requests

from ..exceptions import ContentExtractionError, DownloadURLError, NetworkError, TitleExtractionError
from ..models import Extraction, ExtractionExample, Extractor


class TorahAnytimeExtractor(Extractor):
    """Extract audio content from TorahAnytime.com.

    This extractor handles URLs from www.torahanytime.com and extracts MP3 download
    links along with their associated titles from the page's JavaScript content.
    """

    EXAMPLES = [  # noqa: RUF012
        ExtractionExample(
            name="main_page",
            url="https://torahanytime.com/lectures/335042",
            download_url="https://dl.torahanytime.com/mp3/335042--____10_04_2024__ee9743cb-5d09-4ffc-a3e3-1156e10e8944.mp4.mp3",
            title="Aish Kodesh- Toldot, 5702, When It's Hard to Thank Hashem (2021/22 Series- Enhanced III)",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="short_link",
            url="https://MyTAT.me/a335042",
            download_url="https://dl.torahanytime.com/mp3/335042--____10_04_2024__ee9743cb-5d09-4ffc-a3e3-1156e10e8944.mp4.mp3",
            title="Aish Kodesh- Toldot, 5702, When It's Hard to Thank Hashem (2021/22 Series- Enhanced III)",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="invalid_link",
            url="https://torahanytime.com/whatever/0000000",
            download_url="",
            title="",
            file_format="",
            valid=False,
        ),
    ]

    # URL pattern for TorahAnytime.com pages
    URL_PATTERN = re.compile(r"https?://(?:www\.)?torahanytime\.com/")
    # URL pattern for MyTAT.me pages
    MYTAT_URL_PATTERN = re.compile(r"https?://(?:www\.)?MyTAT\.me/")

    # Pattern to find download URL in script tags
    DOWNLOAD_URL_PATTERN = re.compile(r'"audio_url\\?":\\?"(https.*?)"')

    @property
    def url_patterns(self) -> list[Pattern]:
        """Return the URL pattern(s) that this extractor can handle.

        Returns:
            List[Pattern]: List of compiled regex patterns matching TorahAnytime.com URLs
        """
        return [self.URL_PATTERN, self.MYTAT_URL_PATTERN]

    def extract(self, url: str) -> Extraction:
        """Extract download URL and title from a TorahAnytime.com page.

        Args:
            url: The TorahAnytime.com URL to extract from

        Returns:
            Extraction: Object containing the download URL and title

        Raises:
            ValueError: If the URL is invalid or content cannot be extracted
            requests.RequestException: If there are network-related issues
        """
        try:
            response = requests.get(url, timeout=30, headers={"User-Agent": "torah-dl/1.0"})
            response.raise_for_status()
        except (requests.RequestException, requests.HTTPError) as e:
            raise NetworkError(str(e)) from e  # pragma: no cover

        # Extract download URL
        match = self.DOWNLOAD_URL_PATTERN.search(response.text)
        if not match:
            raise DownloadURLError()

        download_url = match.group(1).replace("\\", "")

        file_name = download_url.split("/")[-1]

        # Extract and decode title
        try:
            title_match = re.search(r'\\"title\\":\\"(.*?)\\"', response.text)
            title = title_match.group(1) if title_match else file_name.split(".")[0]

        except (UnicodeError, IndexError) as e:
            raise TitleExtractionError(str(e)) from e

        if not download_url or not title:
            raise ContentExtractionError()

        return Extraction(download_url=download_url, title=title, file_format="audio/mp3", file_name=file_name)
