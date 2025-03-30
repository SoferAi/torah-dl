from .extract import EXTRACTORS


def list_extractors() -> dict[str, str]:
    """List all available extractors."""
    return {extractor.name: extractor.homepage for extractor in EXTRACTORS}
