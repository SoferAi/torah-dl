from .exceptions import ExtractorNotFoundError
from .extractors import YutorahExtractor
from .models import Extraction

EXTRACTORS = [YutorahExtractor()]


def extract(url: str) -> Extraction:
    for extractor in EXTRACTORS:
        if extractor.can_handle(url):
            return extractor.extract(url)

    raise ExtractorNotFoundError(url)
