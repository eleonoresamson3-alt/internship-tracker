"""Phenom People career sites — reads the search data embedded in the page.

Phenom pages ship their search results as JSON inside `phApp.ddo = {...};`.

params:
  base: site root including locale, e.g. https://jobs.example.com/global/en
"""

import json
from urllib.parse import quote

from .base import AdapterError, RawJob, dedupe_raw, iso_date, require, search_terms
from .. import config
from ..geo import normalize_country

PAGE = 10


def extract_ddo(html: str) -> dict:
    start = html.find("phApp.ddo")
    if start < 0:
        raise AdapterError("phApp.ddo not found: not a Phenom page or layout changed")
    start = html.find("{", start)
    depth, in_str, escape = 0, False, False
    for i in range(start, len(html)):
        ch = html[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(html[start:i + 1])
    raise AdapterError("could not parse phApp.ddo")


def fetch(target, http):
    (base,) = require(target, "base")
    base = base.rstrip("/")
    jobs = []
    for term in search_terms(target):
        for page in range(config.MAX_PAGES_PER_TERM):
            html = http.get(f"{base}/search-results?keywords={quote(term)}&from={page * PAGE}&s=1").text
            search = extract_ddo(html).get("eagerLoadRefineSearch", {})
            items = (search.get("data") or {}).get("jobs", []) or []
            for item in items:
                country = normalize_country(item.get("country", ""))
                locations = item.get("multi_location") or [item.get("location") or item.get("cityStateCountry", "")]
                jobs.append(RawJob(
                    title=item.get("title", ""),
                    url=f"{base}/job/{item.get('jobId')}",
                    location="; ".join(filter(None, locations)),
                    native_id=str(item.get("jobId", "")),
                    posted_at=iso_date(item.get("postedDate")),
                    countries=[country] if country else [],
                    employment_type=item.get("type", "") or "",
                ))
            if not items or (page + 1) * PAGE >= (search.get("totalHits") or 0):
                break
    return dedupe_raw(jobs)
