import pytest

from torah_dl.core.extractors.yutorah import YutorahExtractor


@pytest.mark.parametrize(
    ("url", "shiur_id"),
    [
        ("https://www.yutorah.org/lectures/details?shiurid=1117409", "1117409"),
        ("https://yutorah.org/lectures/details?shiurID=1163252", "1163252"),
        ("https://v4.yutorah.org/lectures/details?shiurId=1148315", "1148315"),
        ("https://www.yutorah.org/lectures/1116616/Praying-for-Rain", "1116616"),
        ("https://classic.yutorah.org/lectures/lecture_iframe.cfm/1116616", "1116616"),
        ("https://classic.yutorah.org/lectures/lecture.cfm/1116616", "1116616"),
        ("https://yutorah.org/sidebar/lecturedata/1116616", "1116616"),
    ],
)
def test_extract_shiur_id_from_yutorah_url_variants(url: str, shiur_id: str):
    assert YutorahExtractor()._extract_shiur_id(url) == shiur_id


def test_can_handle_current_yutorah_url_variants():
    extractor = YutorahExtractor()

    assert extractor.can_handle("https://yutorah.org/lectures/details?shiurID=1163252")
    assert extractor.can_handle("https://v4.yutorah.org/lectures/details?shiurID=1148315")
    assert extractor.can_handle("https://classic.yutorah.org/lectures/lecture_iframe.cfm/1116616")
    assert not extractor.can_handle("https://www.yutorah.org/series/bmp-shiurim")


def test_extract_uses_case_insensitive_shiur_id_query(monkeypatch):
    requested: dict[str, str] = {}

    class Response:
        text = """
        <html>
            <head><title>YUTorah Online - Sample Shiur (Rabbi Example)</title></head>
            <body>https://download.yutorah.org/2026/1/1163252/sample-shiur.mp3</body>
        </html>
        """

        def raise_for_status(self):
            pass

    def fake_get(url: str, timeout: int, headers: dict[str, str]):
        requested["url"] = url
        requested["user_agent"] = headers["User-Agent"]
        assert timeout == 30
        return Response()

    monkeypatch.setattr("torah_dl.core.extractors.yutorah.requests.get", fake_get)

    extraction = YutorahExtractor().extract("https://yutorah.org/lectures/details?shiurID=1163252")

    assert requested == {
        "url": "https://classic.yutorah.org/lectures/lecture_iframe.cfm/1163252",
        "user_agent": "torah-dl/1.0",
    }
    assert extraction.download_url == "https://download.yutorah.org/2026/1/1163252/sample-shiur.mp3"
    assert extraction.file_name == "sample-shiur.mp3"
    assert extraction.title == "Sample Shiur"
    assert extraction.file_format == "audio/mp3"
