import pytest

from torah_dl import extract
from torah_dl.core.exceptions import ExtractorNotFoundError


def test_extract():
    url = "https://www.yutorah.org/lectures/1116616/Praying-for-Rain-and-the-International-Traveler"
    download_url = "https://download.yutorah.org/2024/986/1116616/praying-for-rain-and-the-international-traveler.mp3"

    title = "Praying for Rain and the International Traveler"
    file_format = "mp3"

    extraction = extract(url)
    assert extraction.download_url == download_url
    assert extraction.title == title
    assert extraction.file_format == file_format


def test_extract_failed():
    with pytest.raises(ExtractorNotFoundError):
        extract("https://www.gashmius.xyz/")
