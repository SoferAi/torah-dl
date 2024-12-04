from pathlib import Path

import requests

from .exceptions import DownloadError


def download(url: str, output_path: Path, timeout: int = 30):
    """Download a file from a given URL and save it to the specified output path.

    Args:
        url: The URL to download from
        output_path: The path to save the downloaded file to
        timeout: The timeout for the request
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

    except requests.RequestException as e:
        raise DownloadError(url) from e

    with open(output_path, "wb") as f:
        f.write(response.content)
