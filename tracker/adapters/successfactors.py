"""SAP SuccessFactors Recruiting Marketing ("RMK") career sites — HTML search pages.

SuccessFactors does not offer a public JSON API for candidates, so the
standard search result table is parsed.

params:
  base: site root, e.g. https://jobs.example.com
"""

import re
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup

from .base import RawJob, dedupe_raw, require, search_terms
from .. import config

PAGE = 25


def parse_results(html: str, base: str):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for row in soup.select("tr.data-row"):
        link = row.select_one("a.jobTitle-link")
        if not link:
            continue
        loc = row.select_one("span.jobLocation")
        url = urljoin(base, link["href"])
        match = re.search(r"/(\d+)/?$", url)
        jobs.append(RawJob(
            title=link.get_text(strip=True),
            url=url,
            location=loc.get_text(" ", strip=True) if loc else "",
            native_id=match.group(1) if match else url,
        ))
    label = soup.select_one(".paginationLabel")
    total = 0
    if label:
        numbers = re.findall(r"\d+", label.get_text())
        total = int(numbers[-1]) if numbers else 0
    return jobs, total


def fetch(target, http):
    (base,) = require(target, "base")
    base = base.rstrip("/")
    jobs = []
    for term in search_terms(target):
        for page in range(config.MAX_PAGES_PER_TERM):
            html = http.get(f"{base}/search/?q={quote(term)}&startrow={page * PAGE}").text
            found, total = parse_results(html, base)
            jobs.extend(found)
            if not found or (page + 1) * PAGE >= total:
                break
    return dedupe_raw(jobs)
