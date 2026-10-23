"""Eightfold AI career sites — JSON search API used by the public page.

params:
  host: e.g. careers.example.com or example.eightfold.ai
  domain: company domain passed to the API, e.g. example.com
"""

from urllib.parse import quote

from .base import RawJob, dedupe_raw, iso_date, require, search_terms
from .. import config

PAGE = 10


def fetch(target, http):
    host, domain = require(target, "host", "domain")
    jobs = []
    for term in search_terms(target):
        for page in range(config.MAX_PAGES_PER_TERM):
            url = (f"https://{host}/api/apply/v2/jobs?domain={quote(domain)}"
                   f"&query={quote(term)}&start={page * PAGE}&num={PAGE}")
            data = http.get_json(url)
            positions = data.get("positions", []) or []
            for pos in positions:
                locations = pos.get("locations") or [pos.get("location", "")]
                jobs.append(
                    RawJob(
                        title=pos.get("name", ""),
                        url=pos.get("canonicalPositionUrl")
                        or f"https://{host}/careers?pid={pos.get('id')}&domain={domain}",
                        location="; ".join(filter(None, locations)),
                        native_id=str(pos.get("id", "")),
                        posted_at=iso_date(pos.get("t_create")),
                    )
                )
            if not positions or (page + 1) * PAGE >= (data.get("count") or 0):
                break
    return dedupe_raw(jobs)
