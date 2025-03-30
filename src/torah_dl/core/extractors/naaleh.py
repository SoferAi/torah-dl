import re
from re import Pattern
from typing import cast
from urllib.parse import parse_qs, quote, urlparse

from typing_extensions import override
import requests
from bs4 import BeautifulSoup, Tag

from ..exceptions import DownloadURLError, NetworkError
from ..models import Extraction, ExtractionExample, Extractor


class NaalehExtractor(Extractor):
    """Extract audio content from Naaleh.com.

    This extractor handles URLs from naaleh.com and extracts audio download
    links using the JWPlayer media key along with their titles.
    """

    name: str = "Naaleh"
    homepage: str = "https://naaleh.com"

    EXAMPLES = [  # noqa: RUF012
        ExtractionExample(
            name="main_page",
            url="https://www.naaleh.com/torah_library/?post_id=34538",
            download_url="https://www.naaleh.com/file_downloader/?file_url=https://cdn.jwplayer.com/videos/Md9qaTch.m4a&title=Unlocking%20the%20order%20of%20Seder%20Night.mp3",
            title="Unlocking the order of Seder Night",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="invalid_link",
            url="https://www.naaleh.com/torah_library/?post_id=00000",
            download_url="",
            title="",
            file_format="",
            valid=False,
        ),
    ]

    URL_PATTERN = re.compile(r"https?://(?:www\.)?naaleh\.com/")

    @property
    @override
    def url_patterns(self) -> list[Pattern[str]]:
        """Return the URL pattern(s) that this extractor can handle.

        Returns:
            List[Pattern]: List of compiled regex patterns matching Naaleh.com URLs
        """
        return [self.URL_PATTERN]

    @override
    def extract(self, url: str) -> Extraction:
        """Extract download URL and title from a Naaleh.com page.

        Args:
            url: The Naaleh.com URL to extract from

        Returns:
            Extraction: Object containing the download URL and title

        Raises:
            NetworkError: If there are network-related issues
            DownloadURLError: If the download URL cannot be found
        """
        # Extract post_id from URL
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        post_id = query_params.get("post_id", [""])[0]
        if not post_id:
            raise DownloadURLError()

        try:
            response = requests.get(url, timeout=30, headers={"User-Agent": "torah-dl/1.0"})
            response.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(str(e)) from e

        soup = BeautifulSoup(response.content, "html.parser")

        # Find the media container element that has the JWPlayer data and matching post_id
        media_element = soup.find(attrs={"data-jwplayer-media-key": True, "data-post-id": post_id})
        if not media_element or not isinstance(media_element, Tag):
            raise DownloadURLError()

        media_key = cast(str, media_element.get("data-jwplayer-media-key"))
        title = cast(str, media_element.get("data-post-title"))
        if not media_key or not title:
            raise DownloadURLError()

        # Construct the download URL using the JWPlayer media key
        jwplayer_url = f"https://cdn.jwplayer.com/videos/{media_key}.m4a"
        encoded_title = quote(f"{title}.mp3")
        download_url = f"https://www.naaleh.com/file_downloader/?file_url={jwplayer_url}&title={encoded_title}"

        return Extraction(download_url=download_url, title=title, file_format="audio/mp3", file_name=f"{title}.mp3")
