import re
from re import Pattern

from ..models import Extraction, ExtractionExample, Extractor
from ._ou import extract_canonical_media


class AllMishnahExtractor(Extractor):
    """Extract AllMishnah posts through their canonical OU Torah resource."""

    name: str = "AllMishnah"
    homepage: str = "https://allmishnah.org"

    EXAMPLES = [  # noqa: RUF012
        ExtractionExample(
            name="main_page",
            url="https://allmishnah.org/p/201079",
            download_url="https://media.ou.org/torah/4885/201079/201079.mp3",
            title="Bava Metzia 1:1",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="invalid_link",
            url="https://allmishnah.org/p/000000",
            download_url="",
            title="",
            file_format="",
            valid=False,
        ),
    ]

    URL_PATTERN = re.compile(r"https?://(?:www\.)?allmishnah\.org/p/")

    @property
    def url_patterns(self) -> list[Pattern]:
        return [self.URL_PATTERN]

    def extract(self, url: str) -> Extraction:
        return extract_canonical_media(url)
