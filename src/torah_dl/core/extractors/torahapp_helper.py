from urllib.parse import urlparse, ParseResult, unquote
import urllib.request
import re
import json
import xml.etree.ElementTree as ET

PODCAST_ID_PATTERN = re.compile(r"\/p\/([^\/]+)")
EPISODE_ID_PATTERN = re.compile(r"\/e\/([^\/]+)")
PODCAST_ID_GET_PATTERN = re.compile(r"p=([^\/\&]+)")
EPISODE_ID_GET_PATTERN = re.compile(r"e=([^\/\&]+)")

# dict mapping podcast_id to rss_url
podcasts_to_rss = None


# get 'e' or 'p' value from parsed url
# Example: https://torahapp.org/share/p/YU_80714_all/e/yu:1021736
# getting podcast_id=YU_80714_all and episode_id=yu:1021736
def _get_value(parsed: ParseResult, path_pattern: re.Pattern[str], get_pattern: re.Pattern[str]) -> str:
    results = set()
    results.update(re.findall(path_pattern, parsed.path))
    # unquote() used to convert 'http%3A%2F%2Foutorah.org%2Fp%2F81351' =>
    # 'http://outorah.org/p/81351'
    results.update([unquote(x) for x in re.findall(get_pattern, parsed.query)])

    if len(results) > 1:
        raise Exception('more than one id found')
    elif len(results) == 0:
        raise Exception('no id found: %s' % str(parsed))

    return str(results.pop()).strip()


def _get_podcast_metadata():
    global podcasts_to_rss
    if podcasts_to_rss:
        # avoid redownloading file
        return

    # print('fetching podcasts_metadata')
    req = urllib.request.Request(
        'https://feeds.thetorahapp.org/data/podcasts_metadata.min.json',
        data=None,
    )
    with urllib.request.urlopen(req) as f:
        html = f.read()
        data = json.loads(html)

    podcasts_to_rss = {x['pId']: x['u'] for x in data['podcasts']}
    # Topic title is the "title" for the given podcast series
    # podcasts_to_topic_title = {x['pId']: x['tt'] for x in data['podcasts']}


def get_link_info(url: str) -> tuple:
    _get_podcast_metadata()
    parsed = urlparse(url)

    podcast_id = _get_value(parsed, PODCAST_ID_PATTERN, PODCAST_ID_GET_PATTERN)
    episode_id = _get_value(parsed, EPISODE_ID_PATTERN, EPISODE_ID_GET_PATTERN)

    rss = podcasts_to_rss[podcast_id]
    root = _get_xml_file(rss)
    result = _get_download_link(root, episode_id)
    # print(parsed.path, parsed.query, podcast_id,
    #       episode_id, podcasts_to_rss[podcast_id], result)
    return result


def _get_xml_file(rss_url: str) -> ET.Element:
    req = urllib.request.Request(
        rss_url,
        data=None,
    )
    with urllib.request.urlopen(req) as f:
        html = f.read().decode('utf-8')
        html = html.replace('&feature=youtu.be</guid>', '</guid>')
        root = ET.fromstring(html)
    return root


def _get_download_link(root: ET.Element, episode_id: str) -> tuple:
    items = root.findall('channel/item')
    for item in items:
        guid = item.find('guid').text
        if guid == episode_id:
            enclosure = item.find('enclosure')
            # use this to determine mp3 or whatever
            enclosure_type = enclosure.get('type')
            # ex. http://outorah.org/p/81351 => http:__outorah.org_p_81351
            file_name = guid.replace('/', '_')
            return (enclosure.get('url'), enclosure_type, item.find('title').text, file_name)
    return None


test_urls = [
    'https://torahapp.org/share/p/YU_80714_all/e/yu:1021736',
    'https://thetorahapp.org/share/p/YU_80714_all/e/yu:1021737',
    'https://torahapp.org/share/p/OU_4106?e=http%3A%2F%2Foutorah.org%2Fp%2F81351',
]

if __name__ == '__main__':
    for url in test_urls:
        print(get_link_info(url))
