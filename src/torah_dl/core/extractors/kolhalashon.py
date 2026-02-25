import re
from re import Pattern
from urllib.parse import parse_qs, urlparse

import requests

from ..exceptions import DownloadURLError, NetworkError
from ..models import Extraction, ExtractionExample, Extractor


class KolHalashonExtractor(Extractor):
    """Extract audio content from kolhalashon.com."""

    name: str = "Kol Halashon"
    homepage: str = "https://www.kolhalashon.com"

    EXAMPLES = [  # noqa: RUF012
        ExtractionExample(
            name="play_shiur_url",
            url="https://www.kolhalashon.com/new/Media/PlayShiur.aspx?FileName=34412186&English=True&Lang=English",
            download_url="https://www.kolhalashon.com/mp3/NewArchive/34412/34412186.mp3",
            title="Shiur 34412186",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="invalid_file_id",
            url="https://www.kolhalashon.com/new/Media/PlayShiur.aspx?FileName=00000000&English=True&Lang=English",
            download_url="",
            title="",
            file_format="",
            valid=False,
        ),
    ]

    URL_PATTERN = re.compile(r"https?://(?:www\.)?kolhalashon\.com/")
    FILE_ID_PATTERN = re.compile(r"(?<!\d)(\d{8})(?!\d)")

    @property
    def url_patterns(self) -> list[Pattern]:
        return [self.URL_PATTERN]

    def _extract_file_id(self, url: str) -> str | None:
        query = parse_qs(urlparse(url).query)
        if file_name_values := query.get("FileName"):
            file_id = file_name_values[0].strip()
            if self.FILE_ID_PATTERN.fullmatch(file_id):
                return file_id

        if match := self.FILE_ID_PATTERN.search(url):
            return match.group(1)

        return None

    def _build_download_url(self, file_id: str) -> str:
        # Kol Halashon serves downloadable audio under /mp3/NewArchive/{first5}/{full_id}.mp3
        return f"https://www.kolhalashon.com/mp3/NewArchive/{file_id[:5]}/{file_id}.mp3"

    def extract(self, url: str) -> Extraction:
        if not (file_id := self._extract_file_id(url)):
            raise DownloadURLError()

        download_url = self._build_download_url(file_id)

        try:
            response = requests.head(
                download_url,
                timeout=20,
                headers={"User-Agent": "torah-dl/1.0"},
                allow_redirects=True,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(str(e)) from e  # pragma: no cover

        if "audio/" not in response.headers.get("content-type", "").lower():
            raise DownloadURLError()

        return Extraction(
            download_url=download_url,
            title=f"Shiur {file_id}",
            file_format="audio/mp3",
            file_name=f"{file_id}.mp3",
        )
