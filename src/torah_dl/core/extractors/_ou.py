import json
import re
from collections.abc import Iterator
from typing import Any

import requests
from bs4 import BeautifulSoup

from ..exceptions import DownloadURLError, NetworkError
from ..models import Extraction

POST_ID_PATTERN = re.compile(r"/p/(?P<post_id>\d+)(?=[/?#]|$)")
ESCAPED_SLASH_PATTERN = re.compile(r"\\u002[fF]")
CANONICAL_HOST = "https://outorah.org"
REQUEST_HEADERS = {"User-Agent": "torah-dl/1.0"}
ERR_POST_ID = "Could not extract OU post ID from URL"
ERR_MEDIA = "Could not extract media for OU post"


def canonical_post_url(url: str) -> str:
    """Return the canonical OU Torah URL for any OU-family post URL."""
    post_id_match = POST_ID_PATTERN.search(url)
    if not post_id_match:
        raise DownloadURLError(ERR_POST_ID)

    return f"{CANONICAL_HOST}/p/{post_id_match.group('post_id')}"


def extract_canonical_media(url: str) -> Extraction:
    """Resolve an OU-family post through its canonical OU Torah page."""
    canonical_url = canonical_post_url(url)
    try:
        response = requests.get(canonical_url, timeout=30, headers=REQUEST_HEADERS)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise NetworkError(str(exc)) from exc

    html = response.content.decode("utf-8", errors="replace")
    soup = BeautifulSoup(response.content, "html.parser")
    extraction = extract_structured_media(canonical_url, html, soup)
    if not extraction:
        raise DownloadURLError(ERR_MEDIA)

    return extraction


def extract_structured_media(url: str, html: str, soup: BeautifulSoup) -> Extraction | None:
    """Extract an OU media post from the structured data used by the Nuxt sites."""
    post_id_match = POST_ID_PATTERN.search(url)
    if not post_id_match:
        return None

    post_id = post_id_match.group("post_id")
    normalized_html = ESCAPED_SLASH_PATTERN.sub("/", html).replace(r"\/", "/")
    media_url_pattern = re.compile(
        rf"https://media\.ou\.org/torah/\d+/{re.escape(post_id)}/{re.escape(post_id)}\.(?:mp3|mp4)"
    )
    media_url_match = media_url_pattern.search(normalized_html)
    title = _extract_json_ld_title(soup)

    if not media_url_match or not title:
        return None

    download_url = media_url_match.group(0)
    extension = download_url.rsplit(".", maxsplit=1)[-1].lower()
    file_format = "audio/mp3" if extension == "mp3" else "video/mp4"

    return Extraction(
        download_url=download_url,
        title=title,
        file_format=file_format,
        file_name=download_url.rsplit("/", maxsplit=1)[-1],
    )


def _extract_json_ld_title(soup: BeautifulSoup) -> str | None:
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue

        for item in _iter_json_objects(data):
            media_type = item.get("@type")
            if isinstance(media_type, str):
                media_types = {media_type}
            elif isinstance(media_type, list):
                media_types = {value for value in media_type if isinstance(value, str)}
            else:
                media_types = set()

            title = item.get("name")
            if media_types.intersection({"AudioObject", "VideoObject"}) and isinstance(title, str) and title.strip():
                return title.strip()

    return None


def _iter_json_objects(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _iter_json_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_json_objects(child)
