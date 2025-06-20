import re
import urllib.parse
from re import Pattern

import requests
from bs4 import BeautifulSoup

from ..exceptions import DownloadURLError, NetworkError
from ..models import Extraction, ExtractionExample, Extractor


class AllParshaExtractor(Extractor):
    """Extract audio/video content from AllParsha.org.

    This extractor handles URLs from allparsha.org and constructs MP3/MP4 download
    links using the series title and post-title from the page content.
    """

    name: str = "AllParsha"
    homepage: str = "https://allparsha.org"

    EXAMPLES = [  # noqa: RUF012
        ExtractionExample(
            name="main_page",
            url="https://allparsha.org/p/197738",
            download_url="https://outorah.org/download?title=Aliya%20Outlines%20-%20Mishpatim%206%20-%20The%20Angel%20Leading%20to%20the%20Land&s3Url=https%3A//media.ou.org/torah/4134/197738/197738.mp3",
            title="Aliya Outlines - Mishpatim 6 - The Angel Leading to the Land",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="another_page",
            url="https://allparsha.org/p/85859",
            download_url="https://outorah.org/download?title=The%20Quick%20Parsha%20with%20Rabbi%20Zecharia%20Resnik%20-%20Shelach%20-%20Shishi&s3Url=https%3A//media.ou.org/torah/4106/85859/85859.mp3",
            title="The Quick Parsha with Rabbi Zecharia Resnik - Shelach - Shishi",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="invalid_link",
            url="https://allparsha.org/p/000000",
            download_url="",
            title="",
            file_format="",
            valid=False,
        ),
    ]

    # URL pattern for AllParsha.org pages
    URL_PATTERN = re.compile(r"https?://(?:www\.)?allparsha\.org/")

    @property
    def url_patterns(self) -> list[Pattern]:
        """Return the URL pattern(s) that this extractor can handle.

        Returns:
            List[Pattern]: List of compiled regex patterns matching AllParsha.org URLs
        """
        return [self.URL_PATTERN]

    def extract(self, url: str) -> Extraction:
        """Extract download URL and title from an AllParsha.org page.

        Args:
            url: The AllParsha.org URL to extract from

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

        # Extract the post-ID from the URL
        post_id_match = re.search(r"/p/(\d+)$", url)
        if not post_id_match:
            raise DownloadURLError("Could not extract post ID from URL")
        
        post_id = post_id_match.group(1)

        # Try to find the series title and post-title
        series_title = self._extract_series_title(soup)
        post_title = self._extract_post_title(soup)
        
        if not series_title or not post_title:
            raise DownloadURLError("Could not extract series title or post title")

        # Construct the full title
        full_title = f"{series_title} - {post_title}"
        
        # URL encode the title for the download URL
        encoded_title = urllib.parse.quote(full_title)
        
        # Construct the s3Url (assuming the pattern from the example)
        # Pattern to follow: https://media.ou.org/torah/{series_id}/{post_id}/{post_id}.mp3
        series_id = self._extract_series_id(soup, post_id)
        
        s3_url = f"https://media.ou.org/torah/{series_id}/{post_id}/{post_id}.mp3"
        
        # Construct the full download URL
        download_url = f"https://outorah.org/download?title={encoded_title}&s3Url={urllib.parse.quote(s3_url)}"
        
        file_format = "audio/mp3"
        file_name = f"{post_id}.mp3"
        
        return Extraction(
            download_url=download_url,
            title=full_title,
            file_format=file_format,
            file_name=file_name
        )

    def _extract_series_title(self, soup: BeautifulSoup) -> str:
        """Extract the series title from the page."""
        # Try to find series title in various locations
        selectors = [
            ".series-title",
            ".series__title", 
            ".breadcrumb a[href*='/series/']",
            ".post__header a[href*='/series/']",
            "a[href*='/series/']"
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text().strip()
                if title:
                    return title
        
        return ""

    def _extract_post_title(self, soup: BeautifulSoup) -> str:
        """Extract the post-title from the page."""
        # Try to find post-title in various locations
        selectors = [
            ".post-title",
            ".post__title",
            "h1",
            ".title",
            ".post-header h1",
            ".post__header h1"
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text().strip()
                if title:
                    return title
        
        return ""

    def _extract_series_id(self, soup: BeautifulSoup, post_id: str) -> str:
        """Extract the series ID from the page or make an educated guess."""
        # Try to extract series ID from series href
        series_link = soup.select_one('a[href*="/series/"]')
        if series_link:
            href = series_link.get("href", "")
            if href and isinstance(href, str):
                series_id_match = re.search(r"/series/(\d+)", href)
                if series_id_match:
                    return series_id_match.group(1)
        
        # If we can't find the series ID, we'll need to make an educated guess
        # Try to find any numeric ID that might be the series ID
        # Look for patterns like "series/4134" or similar
        series_patterns = [
            r'series/(\d+)',
            r'seriesId["\']?\s*:\s*["\']?(\d+)["\']?',
            r'data-series-id["\']?\s*=\s*["\']?(\d+)["\']?'
        ]
        
        html_content = str(soup)
        for pattern in series_patterns:
            match = re.search(pattern, html_content)
            if match:
                return match.group(1)
        
        raise DownloadURLError("Could not extract series ID from page") 