from pathlib import Path

import requests

from .exceptions import DownloadError


def download(url: str, output_path: Path, timeout: int = 30):
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

    except requests.RequestException as e:
        raise DownloadError(url) from e

    with open(output_path, "wb") as f:
        f.write(response.content)
