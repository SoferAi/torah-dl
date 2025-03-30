import re
from re import Pattern

import requests
from bs4 import BeautifulSoup

from ..exceptions import DownloadURLError, NetworkError
from ..models import Extraction, ExtractionExample, Extractor


class TorahDownloadsExtractor(Extractor):
    """Extract audio content from TorahDownloads.com.

    This extractor handles URLs from torahdownloads.com and extracts MP3 download
    links along with their associated titles from various locations in the page.
    """

    name: str = "TorahDownloads"
    homepage: str = "https://torahdownloads.com"

    EXAMPLES = [  # noqa: RUF012
        ExtractionExample(
            name="main_page",
            url="https://torahdownloads.com/shiur-23156.html",
            download_url="https://torahcdn.net/tdn/23156.mp3",
            title="Acharei Mos  - Maavir Sedra of Pesukim - Rabbi Dovid Grossman - TD23156",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="intro_to_prayer",
            url="https://torahdownloads.com/shiur-13655.html",
            download_url="https://torahcdn.net/tdn/13655.mp3",
            title="Intro To Prayer - Rabbi Mordechai Becher - TD13655",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="invalid_link",
            url="https://torahdownloads.com/shiur-00000.html",
            download_url="",
            title="",
            file_format="",
            valid=False,
        ),
    ]

    # URL pattern for TorahDownloads.com pages
    URL_PATTERN = re.compile(r"https?://(?:www\.)?torahdownloads\.com/")

    # Pattern to find download URL in script tags
    SCRIPT_URL_PATTERN = re.compile(r"(?:audioUrl|audio_url|url)\s*:\s*['\"]([^'\"]+\.mp3)['\"]", flags=re.IGNORECASE)
    RAW_URL_PATTERN = re.compile(r"https?://[^\"'\s]+\.mp3")

    @property
    def url_patterns(self) -> list[Pattern]:
        """Return the URL pattern(s) that this extractor can handle.

        Returns:
            List[Pattern]: List of compiled regex patterns matching TorahDownloads.com URLs
        """
        return [self.URL_PATTERN]

    def _extract_title(self, soup: BeautifulSoup) -> str | None:
        """Extract the title from the page using various selectors.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            str | None: The extracted title or None if not found
        """
        # Try finding the title in the Details section
        if details := soup.find("div", string="Details"):  # noqa: SIM102
            if length_text := details.find_next(string=lambda text: text and "Length:" in text):  # noqa: SIM102
                # Get all text nodes between Details and Length
                if title_node := length_text.find_previous(
                    string=lambda text: text and text.strip() and "Details" not in text
                ):
                    return title_node.strip()

        # Try finding the title in the breadcrumb/navigation area
        if nav_title := soup.find("div", class_="nav-title"):
            return nav_title.get_text().strip()

        # Try finding any standalone text that looks like a title
        for text in soup.stripped_strings:
            text = text.strip()
            # Skip common non-title text
            if (
                text
                and len(text) > 3
                and "Length:" not in text
                and "Details" not in text
                and "Source" not in text
                and "Speaker" not in text
                and "Category" not in text
                and "Language" not in text
            ):
                return text

        return None

    def extract(self, url: str) -> Extraction:
        """Extract download URL and title from a TorahDownloads.com page.

        Args:
            url: The TorahDownloads.com URL to extract from

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
        html = str(response.content)

        # Extract title first since we'll need it for all cases
        title = self._extract_title(soup)
        download_url = None

        # Try finding audio element first
        media_selector = 'audio source[src*=".mp3"], audio[src*=".mp3"], a[href*=".mp3"]'
        if audio_element := soup.select_one(media_selector):
            download_url = audio_element.get("src") or audio_element.get("href")

        # Try finding download link with various patterns
        if not download_url:
            download_selector = 'a[href*="/download/"], a[href*="getfile"], a[href*="audio"]'
            if download_link := soup.select_one(download_selector):
                download_url = download_link.get("href")

        # Try finding audio URL in script tags
        if not download_url:
            for script in soup.find_all("script"):
                content = script.string or ""
                if media_url_match := self.SCRIPT_URL_PATTERN.search(content):
                    download_url = media_url_match.group(1)
                    break

        # Try finding in the raw HTML for any mp3 URLs
        if not download_url and (media_url_match := self.RAW_URL_PATTERN.search(html)):
            download_url = media_url_match.group(0)

        if download_url:
            file_name = download_url.split("/")[-1]
            return Extraction(download_url=download_url, title=title, file_format="audio/mp3", file_name=file_name)

        raise DownloadURLError()
