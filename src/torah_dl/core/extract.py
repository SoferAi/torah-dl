from .extractors import YutorahExtractor
from .types import Extraction

EXTRACTORS = [YutorahExtractor()]


def extract(url: str) -> Extraction:
    for extractor in EXTRACTORS:
        if extractor.can_handle(url):
            return extractor.extract(url)

    raise ValueError(f"No extractor found for {url}")




