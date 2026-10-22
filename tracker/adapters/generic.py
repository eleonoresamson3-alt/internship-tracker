"""Generic adapter for in-house career sites.

Reads one or more HTML pages and extracts offers from:
  1. schema.org JobPosting data (JSON-LD), when the site publishes it;
  2. otherwise, links whose text looks like an internship title.

params:
  urls: list of page URLs. "{term}" is replaced by each search term
        (see config.SEARCH_TERMS), so search result pages can be used.
  link_pattern: optional regex the link URL must match (e.g. "/job/|JobDetail")
  default_location: location used when the page does not give one
"""

import json
import re
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup

from .base import RawJob, dedupe_raw, iso_date, require, search_terms, title_may_match
from ..geo import normalize_country


def _jsonld_postings(soup):
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, dict):
                if node.get("@type") == "JobPosting":
                    yield node
                stack.extend(v for k, v in node.items() if k == "@graph" or isinstance(v, list))


def _jsonld_location(posting):
    locs = posting.get("jobLocation") or []
    if isinstance(locs, dict):
        locs = [locs]
    names, countries = [], []
    for loc in locs:
        addr = (loc or {}).get("address") or {}
        if isinstance(addr, str):
            names.append(addr)
            continue
        country = addr.get("addressCountry", "")
        if isinstance(country, dict):
            country = country.get("name", "")
        names.append(", ".join(filter(None, [addr.get("addressLocality", ""), country])))
        code = normalize_country(country)
        if code:
            countries.append(code)
    return "; ".join(filter(None, names)), countries


def parse_page(html: str, base_url: str, link_pattern: str = "", default_location: str = ""):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for posting in _jsonld_postings(soup):
        location, countries = _jsonld_location(posting)
        emp = posting.get("employmentType", "")
        jobs.append(RawJob(
            title=posting.get("title", ""),
            url=urljoin(base_url, posting.get("url", "") or base_url),
            location=location or default_location,
            native_id=str((posting.get("identifier") or {}).get("value", "")
                          if isinstance(posting.get("identifier"), dict) else posting.get("identifier", "")),
            posted_at=iso_date(posting.get("datePosted")),
            countries=countries,
            employment_type=" ".join(emp) if isinstance(emp, list) else str(emp),
        ))
    if jobs:
        return jobs

    pattern = re.compile(link_pattern) if link_pattern else None
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        text = " ".join(a.get_text(" ", strip=True).split())
        if not text or len(text) > 200:
            continue
        if pattern and not pattern.search(href):
            continue
        if not title_may_match(text):
            continue
        jobs.append(RawJob(title=text, url=href, location=default_location))
    return jobs


def fetch(target, http):
    (urls,) = require(target, "urls")
    if isinstance(urls, str):
        urls = [urls]
    link_pattern = target.params.get("link_pattern", "")
    default_location = target.params.get("default_location", "")
    jobs = []
    for template in urls:
        pages = ([template.replace("{term}", quote(t)) for t in search_terms(target)]
                 if "{term}" in template else [template])
        for url in pages:
            html = http.get(url).text
            jobs.extend(parse_page(html, url, link_pattern, default_location))
    return dedupe_raw(jobs)
