"""Teamtailor career sites — public RSS feed of open jobs.

params:
  base: career site root, e.g. https://company.teamtailor.com (or a custom domain)
"""

from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

from .base import RawJob, require


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def parse_feed(xml: str):
    root = ElementTree.fromstring(xml)
    jobs = []
    for item in root.iter("item"):
        fields = {_local(child.tag): (child.text or "").strip() for child in item}
        # Locations come as <tt:locations><tt:location><tt:city>...</tt:city>...
        places = [el.text.strip() for el in item.iter()
                  if _local(el.tag) in ("city", "country") and (el.text or "").strip()]
        posted = ""
        if fields.get("pubdate"):
            try:
                posted = parsedate_to_datetime(fields["pubdate"]).date().isoformat()
            except (TypeError, ValueError):
                posted = ""
        jobs.append(RawJob(
            title=fields.get("title", ""),
            url=fields.get("link", ""),
            location=", ".join(dict.fromkeys(places)),
            native_id=fields.get("guid", "") or fields.get("link", ""),
            posted_at=posted,
        ))
    return jobs


def fetch(target, http):
    (base,) = require(target, "base")
    return parse_feed(http.get(f"{base.rstrip('/')}/jobs.rss").text)
