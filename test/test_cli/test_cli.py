import os

from typer.testing import CliRunner

from torah_dl.cli import __version__, app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "SoferAI's Torah Downloader" in result.output


def test_extract_url():
    result = runner.invoke(
        app,
        ["extract", "https://www.kolhalashon.com/new/Media/PlayShiur.aspx?FileName=34412186&English=True&Lang=English"],
    )
    assert result.exit_code == 0
    assert "Shiur 34412186" in result.output


def test_extract_url_only():
    result = runner.invoke(
        app,
        [
            "extract",
            "https://www.kolhalashon.com/new/Media/PlayShiur.aspx?FileName=34412186&English=True&Lang=English",
            "--url-only",
        ],
    )
    assert result.exit_code == 0
    assert "https://www.kolhalashon.com/mp3/NewArchive/34412/34412186.mp3" in result.output


def test_extract_url_failed():
    result = runner.invoke(app, ["extract", "https://www.gashmius.xyz/"])
    assert result.exit_code == 1
    assert "Extractor not found" in result.output


def test_download_url(tmp_path):
    result = runner.invoke(
        app,
        [
            "download",
            "https://www.kolhalashon.com/new/Media/PlayShiur.aspx?FileName=34412186&English=True&Lang=English",
            str(tmp_path / "test.mp3"),
        ],
    )
    assert result.exit_code == 0
    assert os.path.exists(tmp_path / "test.mp3")
