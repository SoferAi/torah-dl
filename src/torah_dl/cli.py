import importlib.metadata
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from torah_dl import download, extract
from torah_dl.core.exceptions import ExtractorNotFoundError

try:
    __version__ = importlib.metadata.version(__package__ or __name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "develop"

app = typer.Typer()
console = Console()


@app.command(name="extract")
def extract_url(
    url: str,
    url_only: Annotated[bool, typer.Option("--url-only", help="Only output the download URL")] = False,
):
    """
    Extract information from a given URL
    """
    try:
        extraction = extract(url)
    except ExtractorNotFoundError:
        typer.echo(f"Extractor not found for URL: {url}", err=True)
        raise typer.Exit(1) from None

    table = Table(box=None, pad_edge=False)
    table.add_column("Title", style="cyan")
    table.add_column("Download URL", style="green")
    table.add_row(extraction.title, extraction.download_url)
    if url_only:
        typer.echo(extraction.download_url)
    else:
        console.print(table)


@app.command(name="download")
def download_url(
    url: Annotated[str, typer.Argument(help="URL to download")],
    output_path: Annotated[Path, typer.Argument(help="Path to save the downloaded file")] = Path("audio"),
):
    """Download a file from a URL and show progress."""
    with console.status("Extracting URL..."):
        extraction = extract(url)
    with console.status("Downloading file..."):
        download(extraction.download_url, output_path)


def version_callback(value: bool):
    """
    print version information to shell
    """
    if value:
        typer.echo(f"torah-dl version: {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def callback(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=version_callback, is_eager=True),
    ] = None,
):
    """
    TODO: add description
    """
    pass


if __name__ == "__main__":
    app()
