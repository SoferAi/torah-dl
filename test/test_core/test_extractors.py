import pytest
from utils import get_all_the_tests

from torah_dl.core.exceptions import TorahDLError
from torah_dl.core.models import Extractor


@pytest.mark.parametrize("extractor, url, download_url, title, file_format, valid", get_all_the_tests())
def test_can_handle(extractor: Extractor, url: str, download_url: str, title: str, file_format: str, valid: bool):
    assert extractor.can_handle(url)


@pytest.mark.parametrize("extractor, url, download_url, title, file_format, valid", get_all_the_tests())
def test_extract(extractor: Extractor, url: str, download_url: str, title: str, file_format: str, valid: bool):
    if not valid:
        with pytest.raises(TorahDLError):
            extractor.extract(url)
    else:
        result = extractor.extract(url)
        assert result.download_url == download_url
        assert result.title == title
        assert result.file_format == file_format
