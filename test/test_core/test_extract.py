import pytest

from torah_dl import extract
from torah_dl.core.exceptions import ExtractorNotFoundError

testdata = [
    pytest.param(
        "https://www.yutorah.org/lectures/1116616/Praying-for-Rain-and-the-International-Traveler",
        "https://download.yutorah.org/2024/986/1116616/praying-for-rain-and-the-international-traveler.mp3",
        "Praying for Rain and the International Traveler",
        "mp3",
        id="yutorah",
    ),
    pytest.param(
        "https://torahanytime.com/lectures/335042",
        "https://dl.torahanytime.com/mp3/335042--____10_04_2024__ee9743cb-5d09-4ffc-a3e3-1156e10e8944.mp4.mp3",
        "Aish Kodesh- Toldot, 5702, When It's Hard to Thank Hashem (2021/22 Series- Enhanced III)",
        "mp3",
        id="torahanytime",
    ),
]


@pytest.mark.parametrize("url, download_url, title, file_format", testdata)
def test_extract(url: str, download_url: str, title: str, file_format: str):
    extraction = extract(url)
    assert extraction.download_url == download_url
    assert extraction.title == title
    assert extraction.file_format == file_format


def test_extract_failed():
    with pytest.raises(ExtractorNotFoundError):
        extract("https://www.gashmius.xyz/")
