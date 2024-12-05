from .exceptions import ExtractorNotFoundError
from .extractors import TorahAnytimeExtractor, YutorahExtractor, TorahAppExtractor
from .models import Extraction

EXTRACTORS = [YutorahExtractor(), TorahAnytimeExtractor(), TorahAppExtractor()]


def extract(url: str) -> Extraction:
    """Extracts the download URL, title, and file format from a given URL."""
    for extractor in EXTRACTORS:
        if extractor.can_handle(url):
            return extractor.extract(url)

    raise ExtractorNotFoundError(url)
