"""Radancy / TalentBrew career sites (e.g. careers.<company>.com/search-jobs).

params:
  base: site root, e.g. https://careers.example.com
"""

from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup

from .base import RawJob, dedupe_raw, require, search_terms
from .. import config


def parse_results(html: str, base: str):
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one("#search-results-list") or soup
    jobs = []
    for a in container.select("a[href*='/job/']"):
        title_el = a.find(["h2", "h3"]) or a
        loc = a.select_one(".job-location") or (a.parent.select_one(".job-location") if a.parent else None)
        url = urljoin(base, a["href"])
        jobs.append(RawJob(
            title=title_el.get_text(" ", strip=True),
            url=url,
            location=loc.get_text(" ", strip=True) if loc else "",
            native_id=a.get("data-job-id", "") or url.rstrip("/").split("/")[-1],
        ))
    return jobs


def fetch(target, http):
    (base,) = require(target, "base")
    base = base.rstrip("/")
    jobs = []
    for term in search_terms(target):
        for page in range(1, config.MAX_PAGES_PER_TERM + 1):
            html = http.get(f"{base}/search-jobs/{quote(term)}?p={page}").text
            found = parse_results(html, base)
            new = [j for j in found if j.url not in {k.url for k in jobs}]
            jobs.extend(new)
            if not new:
                break
    return dedupe_raw(jobs)
