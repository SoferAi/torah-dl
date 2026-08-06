import re
from re import Pattern

from ..models import Extraction, ExtractionExample, Extractor
from ._ou import extract_canonical_media


class AllHalachaExtractor(Extractor):
    """Extract AllHalacha posts through their canonical OU Torah resource."""

    name: str = "AllHalacha"
    homepage: str = "https://allhalacha.org"

    EXAMPLES = [  # noqa: RUF012
        ExtractionExample(
            name="main_page",
            url="https://allhalacha.org/p/23886",
            download_url="https://media.ou.org/torah/3762/23886/23886.mp3",
            title="Mishnah Brurah Yomi - Introduction",
            file_format="audio/mp3",
            valid=True,
        ),
        ExtractionExample(
            name="invalid_link",
            url="https://allhalacha.org/p/000000",
            download_url="",
            title="",
            file_format="",
            valid=False,
        ),
    ]

    URL_PATTERN = re.compile(r"https?://(?:www\.)?allhalacha\.org/p/")

    @property
    def url_patterns(self) -> list[Pattern]:
        return [self.URL_PATTERN]

    def extract(self, url: str) -> Extraction:
        return extract_canonical_media(url)
