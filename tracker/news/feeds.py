"""RSS / Atom feeds: fetch politely and normalise entries."""

from __future__ import annotations

import hashlib
import html
import re
from datetime import datetime, timezone

import feedparser

from ..http import PoliteClient


class FeedError(Exception):
    """A feed answered but could not be used (not a feed, empty...)."""


def _clean(text: str, limit: int = 400) -> str:
    text = re.sub(r"<[^>]+>", " ", html.unescape(text or ""))
    return " ".join(text.split())[:limit]


def _published(entry) -> str:
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        value = entry.get(key)
        if value:
            return datetime(*value[:6], tzinfo=timezone.utc).isoformat(timespec="minutes")
    return ""


def fetch(source: dict, http: PoliteClient) -> list[dict]:
    """Entries of one feed as dicts: id, title, link, published, summary, source."""
    resp = http.get(source["url"], headers={"Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"})
    parsed = feedparser.parse(resp.content)
    if not parsed.entries:
        raise FeedError("no entries (not a feed, or the feed is empty)" + (f": {parsed.bozo_exception}" if parsed.bozo else ""))
    items = []
    for entry in parsed.entries:
        link = entry.get("link", "")
        title = _clean(entry.get("title", ""), 300)
        if not title or not link:
            continue
        items.append({
            "id": hashlib.sha1(link.encode()).hexdigest()[:16],
            "title": title,
            "link": link,
            "published": _published(entry),
            "summary": _clean(entry.get("summary", "") or entry.get("description", "")),
            "source": source["name"],
        })
    return items
