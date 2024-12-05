import re
from re import Pattern
from urllib.parse import urlparse, ParseResult, unquote
import urllib.request
import json
import xml.etree.ElementTree as ET

from ..exceptions import ContentExtractionError, DownloadURLError, NetworkError, TitleExtractionError
from ..models import Extraction, Extractor

# Examples / Testing
# test_urls = [
#     'https://torahapp.org/share/p/YU_80714_all/e/yu:1021736',
#     'https://thetorahapp.org/share/p/YU_80714_all/e/yu:1021737',
#     'https://torahapp.org/share/p/OU_4106?e=http%3A%2F%2Foutorah.org%2Fp%2F81351',
# ]


class TorahAppExtractor(Extractor):
    PODCAST_ID_PATTERN = re.compile(r"\/p\/([^\/]+)")
    EPISODE_ID_PATTERN = re.compile(r"\/e\/([^\/]+)")
    PODCAST_ID_GET_PATTERN = re.compile(r"p=([^\/\&]+)")
    EPISODE_ID_GET_PATTERN = re.compile(r"e=([^\/\&]+)")

    # dict mapping podcast_id to rss_url
    podcasts_to_rss = None

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
        self._get_podcast_metadata()
        parsed = urlparse(url)

        podcast_id = self._get_value(
            parsed, self.PODCAST_ID_PATTERN, self.PODCAST_ID_GET_PATTERN)
        episode_id = self._get_value(
            parsed, self.EPISODE_ID_PATTERN, self.EPISODE_ID_GET_PATTERN)

        rss = self.podcasts_to_rss[podcast_id]
        root = self._get_xml_file(rss)
        result = self._get_download_link(root, episode_id)

        return result

    # get 'e' or 'p' value from parsed url
    # Example: https://torahapp.org/share/p/YU_80714_all/e/yu:1021736
    # getting podcast_id=YU_80714_all and episode_id=yu:1021736
    def _get_value(self, parsed: ParseResult, path_pattern: re.Pattern[str], get_pattern: re.Pattern[str]) -> str:
        results = set()
        results.update(re.findall(path_pattern, parsed.path))
        # unquote() used to convert 'http%3A%2F%2Foutorah.org%2Fp%2F81351' =>
        # 'http://outorah.org/p/81351'
        results.update([unquote(x)
                       for x in re.findall(get_pattern, parsed.query)])

        if len(results) > 1:
            raise ContentExtractionError('more than one id found')
        elif len(results) == 0:
            raise ContentExtractionError('no id found: %s' % str(parsed))

        return str(results.pop()).strip()

    def _get_podcast_metadata(self):
        if self.podcasts_to_rss:
            # avoid redownloading file
            return

        # print('fetching podcasts_metadata')
        req = urllib.request.Request(
            'https://feeds.thetorahapp.org/data/podcasts_metadata.min.json',
            data=None,
        )
        with urllib.request.urlopen(req) as f:
            html = f.read()
            data = json.loads(html)

        self.podcasts_to_rss = {x['pId']: x['u'] for x in data['podcasts']}
        # Topic title is the "title" for the given podcast series
        # podcasts_to_topic_title = {x['pId']: x['tt'] for x in data['podcasts']}

    def _get_xml_file(self, rss_url: str) -> ET.Element:
        req = urllib.request.Request(
            rss_url,
            data=None,
        )
        with urllib.request.urlopen(req) as f:
            html = f.read().decode('utf-8')
            html = html.replace('&feature=youtu.be</guid>', '</guid>')
            root = ET.fromstring(html)
        return root

    def _get_download_link(self, root: ET.Element, episode_id: str) -> Extraction:
        items = root.findall('channel/item')
        for item in items:
            guid = item.find('guid').text
            if guid == episode_id:
                enclosure = item.find('enclosure')
                # use this to determine if mp3 or whatever file type
                enclosure_type = enclosure.get('type')
                # ex. http://outorah.org/p/81351 => http:__outorah.org_p_81351
                file_name = guid.replace('/', '_')
                download_url = enclosure.get('url')
                episode_title = item.find('title').text
                if not download_url or not episode_title:
                    raise ContentExtractionError(
                        'no download_url or no episode_title')
                return Extraction(download_url=download_url, title=episode_title, file_format=enclosure_type, file_name=file_name)
        raise ContentExtractionError('guid not found: %s' % episode_id)
