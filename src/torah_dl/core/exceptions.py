class TorahDLError(Exception):
    """Base exception class for all torah-dl errors."""

    pass


class ExtractionError(TorahDLError):
    """Base class for all extraction-related errors."""

    pass


class NetworkError(ExtractionError):
    """Raised when there are network-related issues during content extraction."""

    pass


class ContentExtractionError(ExtractionError):
    """Raised when required content cannot be extracted from the page."""

    pass


class DownloadURLError(ContentExtractionError):
    """Raised when the download URL cannot be found or extracted."""

    pass


class TitleExtractionError(ContentExtractionError):
    """Raised when the title cannot be found or decoded."""

    pass


class ExtractorNotFoundError(ExtractionError):
    """Raised when no extractor is found for a given URL."""

    pass


class DownloadError(TorahDLError):
    """Raised when there are issues during the download process."""

    pass
