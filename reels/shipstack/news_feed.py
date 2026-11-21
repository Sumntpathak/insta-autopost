"""Automatic tech/science news for the news reels. Headlines come only from the outlets' own RSS feeds
(title, first sentence of the feed summary, link, date) and every reel and caption credits the source.
Nothing is paraphrased or invented. Items older than MAX_AGE_H, over-long headlines and already-posted links are skipped.

    python -m reels.shipstack.news_feed --episode 3 --out reels/out/news.json
"""
import argparse
import datetime as dt
import email.utils
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / 'reels' / 'state.json'
# Rotated by episode so a day's four news reels come from four different outlets.
FEEDS = [
    ('BBC News', 'https://feeds.bbci.co.uk/news/technology/rss.xml'),
    ('Ars Technica', 'https://feeds.arstechnica.com/arstechnica/index'),
    ('NASA', 'https://www.nasa.gov/feed/'),
    ('The Verge', 'https://www.theverge.com/rss/index.xml'),
]
MAX_AGE_H = 48
MAX_HEADLINE = 105
MAX_SUMMARY = 170
UA = 'Mozilla/5.0 (compatible; ShipStackNews/1.0)'


def _clean(text):
    text = html.unescape(re.sub(r'<[^>]+>', ' ', text or ''))
    text = re.sub(r'\s+', ' ', text).strip()
    return re.sub(r'\s+([.,;:!?])', r'\1', text)


ABBREV = {'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'sept', 'oct', 'nov', 'dec', 'mr', 'mrs', 'ms', 'dr', 'st', 'vs',
          'no', 'inc', 'co', 'ltd', 'u.s', 'u.k', 'e.g', 'i.e', 'approx'}


def _first_sentence(text):
    """First sentence, without splitting at abbreviations such as 'Oct.' or 'U.S.'."""
    for m in re.finditer(r'[.!?](?=\s+[A-Z"“‘])', text):
        before = text[:m.start()].split()[-1].lower() if text[:m.start()].split() else ''
        if m.group() == '.' and (before.strip('("“‘') in ABBREV or len(before) == 1):
            continue
        return text[:m.end()]
    return text


def _summary(text):
    text = _clean(text)
    text = re.sub(r'^(Description|Summary)\s*:?\s+', '', text)
    text = re.sub(r'\s*(The post|Read more|Continue reading|\[…\]|\[\.\.\.\]).*$', '', text, flags=re.I).strip()
    if not text or re.search(r'\b(Archive|Submissions|Index)\b.*\b(Calendar|About|Discuss)\b', text):
        return ''       # feed boilerplate, not a summary
    first = _first_sentence(text)
    if len(first) <= MAX_SUMMARY:
        return first
    cut = first[:MAX_SUMMARY].rsplit(' ', 1)[0].rstrip(',;:-')
    return cut + '…'


def _date(text):
    text = (text or '').strip()
    try:
        d = email.utils.parsedate_to_datetime(text)
    except (TypeError, ValueError):
        try:
            d = dt.datetime.fromisoformat(text.replace('Z', '+00:00'))
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def parse(xml_bytes, source):
    """RSS 2.0 or Atom -> [{source, headline, summary, url, published}]"""
    root = ET.fromstring(xml_bytes)
    out = []
    for node in root.iter():
        tag = node.tag.split('}')[-1]
        if tag not in ('item', 'entry'):
            continue
        def get(*names):
            for name in names:       # elements without children are falsy, so test `is not None`, never truthiness
                found = next((c for c in node if c.tag.split('}')[-1] == name), None)
                if found is not None:
                    return found
            return None
        title, link, desc = get('title'), get('link'), get('description', 'summary', 'content')
        pub = get('pubDate', 'published', 'updated')
        url = (link.get('href') if link is not None and link.get('href') else (link.text if link is not None else '')) or ''
        published = _date(pub.text) if pub is not None else None
        if title is None or not url.startswith('https://') or published is None:
            continue
        out.append(dict(source=source, headline=_clean(title.text), summary=_summary(desc.text if desc is not None else ''),
                        url=url.strip(), published=published.isoformat()))
    return out


def fetch(source, url, timeout=20):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return parse(r.read(), source)


def used_urls(path=STATE):
    try:
        posts = json.loads(Path(path).read_text())['posts']
    except (OSError, ValueError, KeyError):
        return set()
    return {p['news_url'] for p in posts.values() if p.get('news_url')}


def pick(episode, items_by_source, used, now=None):
    """Newest unused, fresh, not-too-long item from the outlet for this episode; falls back to the other outlets."""
    now = now or dt.datetime.now(dt.timezone.utc)
    order = [FEEDS[(episode - 1 + k) % len(FEEDS)][0] for k in range(len(FEEDS))]
    for source in order:
        fresh = []
        for it in items_by_source.get(source, []):
            age = (now - dt.datetime.fromisoformat(it['published'])).total_seconds() / 3600
            if 0 <= age <= MAX_AGE_H and it['url'] not in used and 12 <= len(it['headline']) <= MAX_HEADLINE and not it['headline'].startswith('APOD'):
                fresh.append(it)
        if fresh:
            return max(fresh, key=lambda it: it['published'])
    return None


def choose(episode, now=None, used=None):
    items = {}
    for source, url in FEEDS:
        try:
            items[source] = fetch(source, url)
        except Exception as e:      # one outlet being down must not stop the others
            print(f'warning: {source} feed failed: {e}', file=sys.stderr)
    item = pick(episode, items, used if used is not None else used_urls(), now)
    if item is None:
        raise SystemExit('No fresh unused news item in any feed; skipping this slot rather than posting filler.')
    d = dt.datetime.fromisoformat(item['published']).astimezone(dt.timezone(dt.timedelta(hours=5, minutes=30)))
    item['date'] = d.strftime('%d %b %Y').upper()
    item['domain'] = urlparse(item['url']).netloc.removeprefix('www.')
    return item


def caption(item):
    body = item['summary'] + '\n\n' if item['summary'] else ''
    return (f"{item['headline']}\n\n{body}Source: {item['source']} ({item['domain']}) · {item['date'].title()}\n"
            f"Read the full story: {item['url']}\n\nFollow for daily tech news.\n\n"
            'ShipStack Tech News · @shipstack_\n#technews #technology #news #science #ai')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--episode', type=int, default=1)
    ap.add_argument('--out', default='reels/out/news.json')
    a = ap.parse_args()
    item = choose(a.episode)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(item, indent=1, ensure_ascii=False))
    print(item['source'], '|', item['headline'])
