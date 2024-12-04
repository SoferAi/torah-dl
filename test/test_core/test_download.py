import os

import pytest

from torah_dl import download
from torah_dl.core.exceptions import DownloadError


def test_download(tmp_path):
    url = "https://download.yutorah.org/2024/36856/1116233/daily-halachah---collecting-an-amazon-order-on-shabbat.mp3"

    download(url, tmp_path / "test.mp3")
    assert os.path.exists(tmp_path / "test.mp3")
    # TODO: check that it's actually an mp3 file


def test_download_failed(tmp_path):
    with pytest.raises(DownloadError):
        download("https://www.gashmius.xyz/", tmp_path / "test.mp3")
