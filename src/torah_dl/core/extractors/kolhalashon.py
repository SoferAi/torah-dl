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
            title="Q&A w Rabbi Yaron Reuven The Foundation Of Good",
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
    FILE_ID_PATTERN = re.compile(r"(?<!\d)(\d{6,8})(?!\d)")
    PLAY_SHIUR_PATTERN = re.compile(r"/playShiur/(\d{1,8})(?:/|$)", re.IGNORECASE)

    @property
    def url_patterns(self) -> list[Pattern]:
        return [self.URL_PATTERN]

    def _extract_file_id(self, url: str) -> str | None:
        query = parse_qs(urlparse(url).query)
        if file_name_values := query.get("FileName"):
            file_id = file_name_values[0].strip()
            if self.FILE_ID_PATTERN.fullmatch(file_id):
                return file_id

        if match := self.PLAY_SHIUR_PATTERN.search(url):
            file_id = match.group(1).strip()
            if file_id.isdigit():
                return file_id

        if match := self.FILE_ID_PATTERN.search(url):
            return match.group(1)

        return None

    def _build_download_url(self, file_id: str) -> str:
        # regularSite/playShiur URLs can use short numeric ids; the media path uses an 8-digit zero-padded id.
        normalized_id = file_id.zfill(8)
        return f"https://www.kolhalashon.com/mp3/NewArchive/{normalized_id[:5]}/{normalized_id}.mp3"

    def _decode_text_frame(self, frame_payload: bytes) -> str | None:
        """Decode an ID3 text frame payload (without frame header)."""
        if not frame_payload:
            return None
        encoding = frame_payload[0]
        text_data = frame_payload[1:]
        try:
            if encoding == 0:  # ISO-8859-1
                text = text_data.split(b"\x00", 1)[0].decode("latin1", errors="ignore")
            elif encoding == 1:  # UTF-16 with BOM
                text = text_data.decode("utf-16", errors="ignore").split("\x00", 1)[0]
            elif encoding == 2:  # UTF-16BE without BOM
                text = text_data.decode("utf-16-be", errors="ignore").split("\x00", 1)[0]
            else:  # UTF-8
                text = text_data.decode("utf-8", errors="ignore").split("\x00", 1)[0]
        except UnicodeError:
            return None
        cleaned = " ".join(text.strip().split())
        return cleaned or None

    def _extract_title_from_id3(self, download_url: str) -> str | None:
        """Extract title from mp3 ID3 metadata (TIT2 frame)."""
        try:
            response = requests.get(
                download_url,
                timeout=20,
                headers={"User-Agent": "torah-dl/1.0", "Range": "bytes=0-131071"},
            )
            response.raise_for_status()
            data = response.content
        except requests.RequestException:
            return None

        if len(data) < 10 or not data.startswith(b"ID3"):
            return None

        major_version = data[3]
        tag_size = ((data[6] & 0x7F) << 21) | ((data[7] & 0x7F) << 14) | ((data[8] & 0x7F) << 7) | (data[9] & 0x7F)
        tag_data = data[10 : 10 + tag_size]

        offset = 0
        while offset + 10 <= len(tag_data):
            frame_id = tag_data[offset : offset + 4]
            if frame_id == b"\x00\x00\x00\x00":
                break

            if major_version == 4:
                frame_size = (
                    ((tag_data[offset + 4] & 0x7F) << 21)
                    | ((tag_data[offset + 5] & 0x7F) << 14)
                    | ((tag_data[offset + 6] & 0x7F) << 7)
                    | (tag_data[offset + 7] & 0x7F)
                )
            else:
                frame_size = int.from_bytes(tag_data[offset + 4 : offset + 8], byteorder="big")

            if frame_size <= 0:
                break

            frame_payload = tag_data[offset + 10 : offset + 10 + frame_size]
            if frame_id == b"TIT2":
                return self._decode_text_frame(frame_payload)

            offset += 10 + frame_size

        return None

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

        normalized_id = file_id.zfill(8)
        title = self._extract_title_from_id3(download_url) or f"Shiur {normalized_id}"

        return Extraction(
            download_url=download_url,
            title=title,
            file_format="audio/mp3",
            file_name=f"{normalized_id}.mp3",
        )
