import importlib
import inspect
import pkgutil

from . import extractors
from .exceptions import ExtractorNotFoundError
from .models import Extraction, Extractor

# Dynamically build EXTRACTORS list
EXTRACTORS: list[Extractor] = []
for _, name, _ in pkgutil.iter_modules(extractors.__path__):
    module = importlib.import_module(f".{name}", "torah_dl.core.extractors")
    for _, obj in inspect.getmembers(module):
        # Check if it's a class and ends with 'Extractor' (excluding the base class if you have one)
        if inspect.isclass(object=obj) and issubclass(obj, Extractor) and obj is not Extractor:
            EXTRACTORS.append(obj())


def extract(url: str) -> Extraction:
    """Extracts the download URL, title, and file format from a given URL."""
    for extractor in EXTRACTORS:
        if extractor.can_handle(url):
            return extractor.extract(url)

    raise ExtractorNotFoundError(url)


def can_handle(url: str) -> bool:
    """Checks if a given URL can be handled by any extractor."""
    return any(extractor.can_handle(url) for extractor in EXTRACTORS)
