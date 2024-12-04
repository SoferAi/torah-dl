import pytest

from torah_dl.core.exceptions import NetworkError


class TestYutorahExtractor:
    from torah_dl.core.extractors import YutorahExtractor

    extractor = YutorahExtractor()

    testdata = [
        pytest.param(
            "https://www.yutorah.org/lectures/1116616/Praying-for-Rain-and-the-International-Traveler",
            "https://download.yutorah.org/2024/986/1116616/praying-for-rain-and-the-international-traveler.mp3",
            "Praying for Rain and the International Traveler",
            "mp3",
            id="main_page",
        ),
        pytest.param(
            "https://www.yutorah.org/lectures/1117459/",
            "https://download.yutorah.org/2024/986/1117459/davening-with-strep-throat.mp3",
            "Davening with Strep Throat",
            "mp3",
            id="short_link",
        ),
        pytest.param(
            "https://www.yutorah.org/lectures/details?shiurid=1117409",
            "https://download.yutorah.org/2024/21197/1117409/ketubot-42-dechitat-aveilut-1.mp3",
            "Ketubot 42: Dechitat Aveilut (1)",
            "mp3",
            id="shiurid_link",
        ),
    ]

    @pytest.mark.parametrize("url, download_url, title, file_format", testdata)
    def test_can_handle(self, url: str, download_url: str, title: str, file_format: str):
        assert self.extractor.can_handle(url)

    @pytest.mark.parametrize("url, download_url, title, file_format", testdata)
    def test_extract(self, url: str, download_url: str, title: str, file_format: str):
        result = self.extractor.extract(url)
        assert result.download_url == download_url
        assert result.title == title
        assert result.file_format == file_format

    def test_extract_invalid_link(self):
        with pytest.raises(NetworkError):
            self.extractor.extract("https://www.yutorah.org/lectures/details?shiurid=0000000/")
