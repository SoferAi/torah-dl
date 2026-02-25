import os

import pytest

from torah_dl import download
from torah_dl.core.exceptions import DownloadError


def test_download(tmp_path):
    url = "https://www.kolhalashon.com/mp3/NewArchive/34412/34412186.mp3"

    download(url, tmp_path / "test.mp3")
    assert os.path.exists(tmp_path / "test.mp3")
    # TODO: check that it's actually an mp3 file


def test_download_failed(tmp_path):
    with pytest.raises(DownloadError):
        download("https://www.gashmius.xyz/", tmp_path / "test.mp3")
