import re
from re import Pattern

import requests
from bs4 import BeautifulSoup, Tag

from ..exceptions import DownloadURLError, NetworkError
from ..models import Extraction, ExtractionExample, Extractor


class VirtualBeitMidrashExtractor(Extractor):
    """Extract audio mp3 and YouTube video links from etzion.org.il pages."""

    name: str = "Virtual Beit Midrash (Etzion)"
    homepage: str = "https://etzion.org.il"

    # Etzion currently blocks automated HTTP clients behind Cloudflare.
    # Keep these examples for URL matching, but mark as invalid in live tests.
    EXAMPLES = [  # noqa: RUF012
        ExtractionExample(
            name="etzion_audio_page",
            url="https://etzion.org.il/en/tanakh/ketuvim/megillat-ruth/megilat-hahessed-ruth-avraham-and-meaning-hessed",
            download_url="https://traffic.libsyn.com/secure/kmtt/RYEtshalom_megilat-hahessed-ruth-avraham-and-the-meaning-of-hessed.mp3",
            title="Megilat haHessed - Ruth, Avraham and the Meaning of Hessed",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="etzion_video_page",
            url="https://etzion.org.il/en/tanakh/ketuvim/sefer-tehillim/tehillim-center-tefilla",
            download_url="https://www.youtube.com/embed/-l6Tlqg2syc?wmode=opaque",
            title="Tehillim at the Center of Tefilla",
            file_format="video/youtube",
            valid=True,
        ),
        ExtractionExample(
            name="etzion_audio_page_2",
            url="https://etzion.org.il/en/talmud/seder-zeraim/massekhet-berakhot/connecting-redemption-tefilla",
            download_url="http://traffic.libsyn.com/kmtt/wed_10_05_06-ebick_berachot01.mp3",
            title="Connecting the Redemption to Tefilla",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="invalid_link",
            url="https://etzion.org.il/en/invalid-page",
            download_url="",
            title="",
            file_format="",
            valid=False,
        ),
    ]

    URL_PATTERN = re.compile(r"https?://(www\.)?etzion\.org\.il/")
    MP3_PATTERN = re.compile(r'https?://[^"\']+\.mp3')
    YOUTUBE_PATTERN = re.compile(r"https?://www\.youtube\.com/embed/[\w-]+\?wmode=opaque")

    @property
    def url_patterns(self) -> list[Pattern]:
        return [self.URL_PATTERN]

    def extract(self, url: str) -> Extraction:
        try:
            response = requests.get(url, timeout=30, headers={"User-Agent": "torah-dl/1.0"})
            response.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(str(e)) from e

        soup = BeautifulSoup(response.content, "html.parser")

        # Prioritize YouTube embed over MP3
        video_extraction = self._extract_video(soup)
        if video_extraction:
            return video_extraction

        audio_extraction = self._extract_audio(soup, response.text)
        if audio_extraction:
            return audio_extraction

        raise DownloadURLError()

    def _extract_audio(self, soup: BeautifulSoup, html_text: str) -> Extraction | None:
        # Try to find audio mp3 link in <a> tags
        for a in soup.find_all("a", href=True):
            if isinstance(a, Tag):
                href = a.get("href")
                if isinstance(href, str) and self.MP3_PATTERN.match(href):
                    return self._build_audio_extraction(href, soup)
        # Try <audio> tags
        for audio in soup.find_all("audio"):
            if isinstance(audio, Tag):
                src = audio.get("src")
                if isinstance(src, str) and self.MP3_PATTERN.match(src):
                    return self._build_audio_extraction(src, soup)
        # Try searching raw HTML for .mp3
        match = self.MP3_PATTERN.search(html_text)
        if match:
            return self._build_audio_extraction(match.group(0), soup)
        return None

    def _build_audio_extraction(self, audio_link: str, soup: BeautifulSoup) -> Extraction:
        title = ""
        title_tag = soup.find("meta", property="og:title")
        if isinstance(title_tag, Tag) and title_tag.has_attr("content"):
            title = str(title_tag.get("content", ""))
        else:
            title_tag = soup.find("title")
            if isinstance(title_tag, Tag):
                title = title_tag.get_text()
        # Trim at first '|' and strip whitespace
        if "|" in title:
            title = title.split("|", 1)[0].strip()
        file_name = audio_link.split("/")[-1]
        return Extraction(download_url=audio_link, title=title, file_format="audio/mp3", file_name=file_name)

    def _extract_video(self, soup: BeautifulSoup) -> Extraction | None:
        for tag in soup.find_all("iframe"):
            if isinstance(tag, Tag):
                src = tag.get("src")
                if isinstance(src, str) and self.YOUTUBE_PATTERN.match(src):
                    youtube_url = src
                    title = ""
                    title_tag = soup.find("meta", property="og:title")
                    if isinstance(title_tag, Tag) and title_tag.has_attr("content"):
                        title = str(title_tag.get("content", ""))
                    else:
                        title_tag = soup.find("title")
                        if isinstance(title_tag, Tag):
                            title = title_tag.get_text()
                    # Trim at first '|' and strip whitespace
                    if "|" in title:
                        title = title.split("|", 1)[0].strip()
                    return Extraction(
                        download_url=youtube_url, title=title, file_format="video/youtube", file_name=None
                    )
        return None
