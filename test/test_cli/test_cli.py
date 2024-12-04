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
    assert "TODO: add description" in result.output


def test_extract_url():
    result = runner.invoke(app, ["extract", "https://www.yutorah.org/lectures/details?shiurid=1117409"])
    assert result.exit_code == 0
    assert "Ketubot 42: Dechitat Aveilut (1)" in result.output


def test_extract_url_only():
    result = runner.invoke(app, ["extract", "https://www.yutorah.org/lectures/details?shiurid=1117409", "--url-only"])
    assert result.exit_code == 0
    assert "https://download.yutorah.org/2024/21197/1117409/ketubot-42-dechitat-aveilut-1.mp3" in result.output


def test_extract_url_failed():
    result = runner.invoke(app, ["extract", "https://www.gashmius.xyz/"])
    assert result.exit_code == 1
    assert "Extractor not found" in result.output


def test_download_url(tmp_path):
    result = runner.invoke(
        app,
        [
            "download",
            "https://yutorah.org/lectures/1116233/Daily-HalachahCollecting-an-Amazon-Order-on-Shabbat",
            str(tmp_path / "test.mp3"),
        ],
    )
    assert result.exit_code == 0
    assert os.path.exists(tmp_path / "test.mp3")
