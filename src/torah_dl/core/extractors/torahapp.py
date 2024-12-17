import json
import re
import urllib.request
import xml.etree.ElementTree as ET  # noqa: S405
from re import Pattern
from urllib.parse import ParseResult, unquote, urlparse

import defusedxml.ElementTree as DET

from ..exceptions import ContentExtractionError
from ..models import Extraction, ExtractionExample, Extractor


class TorahAppExtractor(Extractor):
    EXAMPLES = [  # noqa: RUF012
        ExtractionExample(
            name="yu_lecture",
            url="https://torahapp.org/share/p/YU_80714_all/e/yu:1021736",
            download_url="https://shiurim.yutorah.net/2022/1109/1021736.MP3",
            title="Berachos 9:1-2",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="yu_lecture_2",
            url="https://thetorahapp.org/share/p/YU_80714_all/e/yu:1021737",
            download_url="https://shiurim.yutorah.net/2022/1109/1021737.MP3",
            title="Berachos 9:3-4",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="ou_lecture",
            url="https://thetorahapp.org/share/p/OU_4106?e=http%3A%2F%2Foutorah.org%2Fp%2F81351",
            download_url="https://media.ou.org/audio/parsha/rabbi-zecharia-resnik/bo-5.mp3",
            title="Bo - Chamishi",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="invalid_link",
            url="https://torahapp.org/share/p/whatever",
            download_url="",
            title="",
            file_format="",
            valid=False,
        ),
    ]

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
    URL_PATTERN = re.compile(r"https?://(?:the)?torahapp\.org", flags=re.IGNORECASE)

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
            url: The torahapp.org URL to extract from

        Returns:
            Extraction: Object containing the download URL and title

        Raises:
            ValueError: If the URL is invalid or content cannot be extracted
            requests.RequestException: If there are network-related issues
        """
        self._get_podcast_metadata()
        parsed = urlparse(url)

        podcast_id = self._get_value(parsed, self.PODCAST_ID_PATTERN, self.PODCAST_ID_GET_PATTERN)
        episode_id = self._get_value(parsed, self.EPISODE_ID_PATTERN, self.EPISODE_ID_GET_PATTERN)

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
        results.update([unquote(x) for x in re.findall(get_pattern, parsed.query)])

        if len(results) > 1:
            raise MoreThanOneIDFoundError()
        elif len(results) == 0:
            raise NoIDFoundError(str(parsed))

        return str(results.pop()).strip()

    def _get_podcast_metadata(self):
        if self.podcasts_to_rss:
            # avoid redownloading file
            return

        # print('fetching podcasts_metadata')
        req = urllib.request.Request(
            "https://feeds.thetorahapp.org/data/podcasts_metadata.min.json",
            data=None,
        )
        # TODO(@herzberg): suspicious-url-open-usage (S310)
        # use a more secure method to fetch the data
        with urllib.request.urlopen(req, context=None) as f:  # noqa: S310
            html = f.read()
            data = json.loads(html)

        self.podcasts_to_rss = {x["pId"]: x["u"] for x in data["podcasts"]}
        # Topic title is the "title" for the given podcast series
        # podcasts_to_topic_title = {x['pId']: x['tt'] for x in data['podcasts']}

    def _get_xml_file(self, rss_url: str) -> ET.Element:
        # TODO(@herzberg): suspicious-url-open-usage (S310)
        # use a more secure method to fetch the data
        req = urllib.request.Request(  # noqa: S310
            str(rss_url),
            data=None,
        )
        # TODO(@herzberg): suspicious-url-open-usage (S310)
        with urllib.request.urlopen(req, context=None) as f:  # noqa: S310
            html = f.read().decode("utf-8")
            html = html.replace("&feature=youtu.be</guid>", "</guid>")
            root = DET.fromstring(html)
        return root

    def _get_download_link(self, root: ET.Element, episode_id: str) -> Extraction:
        items = root.findall("channel/item")
        for item in items:
            guid = item.find("guid").text
            if guid == episode_id:
                enclosure = item.find("enclosure")
                # ex. http://outorah.org/p/81351 => http:__outorah.org_p_81351
                file_name = guid.replace("/", "_")
                download_url = enclosure.get("url")
                episode_title = item.find("title").text
                # use this to determine if mp3 or whatever file type
                file_format = enclosure.get("type")
                if file_format != "audio/mp3":
                    file_format = f"audio/{download_url.split('.')[-1]}"

                if not download_url or not episode_title:
                    raise NoDownloadURLFoundError(episode_id)
                return Extraction(
                    download_url=download_url, title=episode_title, file_format=file_format, file_name=file_name
                )
        raise GUIDNotFoundError(episode_id)


class GUIDNotFoundError(ContentExtractionError):
    def __init__(self, episode_id: str):
        super().__init__(f"guid not found: {episode_id}")


class MoreThanOneIDFoundError(ContentExtractionError):
    def __init__(self, episode_id: str):
        super().__init__(f"more than one id found: {episode_id}")


class NoIDFoundError(ContentExtractionError):
    def __init__(self, episode_id: str):
        super().__init__(f"no id found: {episode_id}")


class NoDownloadURLFoundError(ContentExtractionError):
    def __init__(self, episode_id: str):
        super().__init__(f"no download url found: {episode_id}")
