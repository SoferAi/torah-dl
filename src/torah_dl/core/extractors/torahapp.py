import re
from re import Pattern

from ..exceptions import ContentExtractionError, DownloadURLError, NetworkError, TitleExtractionError
from ..models import Extraction, Extractor
import torahapp_helper


class TorahAppExtractor(Extractor):
    """Extract audio content from TorahApp.org.

    This extractor handles URLs from torahapp.org or thetorahapp.org and extracts MP3 download
    links.
    """

    # URL pattern for torahapp.org pages
    URL_PATTERN = re.compile(
        r"https?://(?:the)?torahapp\.org", flags=re.IGNORECASE)

    # Pattern to find download URL in script tags
    DOWNLOAD_URL_PATTERN = re.compile(
        r'"downloadURL":"(https?://[^\"]+\.mp3)"')

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
            url: The torahapp.org URL to extract from

        Returns:
            Extraction: Object containing the download URL and title

        Raises:
            ValueError: If the URL is invalid or content cannot be extracted
            requests.RequestException: If there are network-related issues
        """
        (download_url, enclosure_type, episode_title,
         file_name) = torahapp_helper.get_link_info(url)

        if not download_url or not episode_title:
            raise ContentExtractionError()

        return Extraction(download_url=download_url, title=episode_title, file_format=enclosure_type, file_name=file_name)
