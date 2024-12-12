import pytest
from utils import get_all_the_tests

from torah_dl import extract
from torah_dl.core.exceptions import ExtractorNotFoundError


@pytest.mark.parametrize("extractor, url, download_url, title, file_format, valid", get_all_the_tests(only_valid=True))
def test_extract(extractor, url: str, download_url: str, title: str, file_format: str, valid: bool):
    extraction = extract(url)
    assert extraction.download_url == download_url
    assert extraction.title == title
    assert extraction.file_format == file_format


def test_extract_failed():
    with pytest.raises(ExtractorNotFoundError):
        extract("https://www.gashmius.xyz/")
