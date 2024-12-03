
import pytest


class TestYutorahExtractor:
    from torah_dl.core.extractors import YutorahExtractor
    extractor = YutorahExtractor()

    def test_can_handle(self):
        assert self.extractor.can_handle("https://www.yutorah.org/")

    def test_extract_main_page(self):
        result = self.extractor.extract("https://www.yutorah.org/lectures/1116616/Praying-for-Rain-and-the-International-Traveler")
        assert result.download_url == "https://download.yutorah.org/2024/986/1116616/praying-for-rain-and-the-international-traveler.mp3"
        assert result.title == "Praying for Rain and the International Traveler"
        assert result.file_format == "mp3"

    def test_extract_short_link(self):
        result = self.extractor.extract("https://www.yutorah.org/lectures/1117459/")
        assert result.download_url == "https://download.yutorah.org/2024/986/1117459/davening-with-strep-throat.mp3"
        assert result.title == "Davening with Strep Throat"
        assert result.file_format == "mp3"

    def test_extract_shiurid_link(self):
        result = self.extractor.extract("https://www.yutorah.org/lectures/details?shiurid=1117409")
        assert result.download_url == "https://download.yutorah.org/2024/21197/1117409/ketubot-42-dechitat-aveilut-1.mp3"
        assert result.title == "Ketubot 42: Dechitat Aveilut (1)"
        assert result.file_format == "mp3"

    def test_extract_invalid_link(self):
        with pytest.raises(ValueError):
            self.extractor.extract("https://www.yutorah.org/lectures/details?shiurid=0000000/")
