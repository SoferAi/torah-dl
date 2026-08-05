import json
import re
from collections.abc import Iterator
from typing import Any

from bs4 import BeautifulSoup

from ..models import Extraction

POST_ID_PATTERN = re.compile(r"/p/(?P<post_id>\d+)(?:/|$)")
ESCAPED_SLASH_PATTERN = re.compile(r"\\u002[fF]")


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
