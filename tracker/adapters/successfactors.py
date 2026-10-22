"""SAP SuccessFactors Recruiting Marketing ("RMK") career sites — HTML search pages.

Classic RMK sites render a result table, which is parsed. Newer "Career Site
Builder" sites render results in JavaScript from an internal JSON endpoint
(/services/recruiting/v1/jobs); when the table is absent, that endpoint is
used with the CSRF token found in the search page, as the page itself does.

params:
  base: site root, e.g. https://jobs.example.com
  locale: locale used by the JSON endpoint (default en_GB)
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


def fetch_csb(target, http, base: str, html: str):
    match = re.search(r"""CSRFToken\s*[=:]\s*["']([^"']+)""", html)
    if not match:
        return []
    locale = target.params.get("locale", "en_GB")
    headers = {"X-CSRF-Token": match.group(1)}
    jobs = []
    for term in search_terms(target):
        for page in range(config.MAX_PAGES_PER_TERM):
            data = http.post_json(f"{base}/services/recruiting/v1/jobs", {
                "locale": locale, "pageNumber": page, "sortBy": "", "keywords": term, "location": "",
                "facetFilters": {}, "brand": "", "skills": [], "categoryId": 0, "alertId": "", "rcmCandidateId": "",
            }, headers=headers)
            results = data.get("jobSearchResult", []) or []
            for item in results:
                job = item.get("response", item)
                job_id = job.get("id", "")
                locations = job.get("jobLocationShort") or job.get("jobLocation") or []
                jobs.append(RawJob(
                    title=job.get("unifiedStandardTitle") or job.get("title", ""),
                    url=f"{base}/job/{job.get('urlTitle', 'job')}/{job_id}-{locale.replace('_', '-')}/",
                    location="; ".join(locations) if isinstance(locations, list) else str(locations),
                    native_id=str(job_id),
                ))
            if not results or len(jobs) >= (data.get("totalJobs") or 0):
                break
    return jobs


def fetch(target, http):
    (base,) = require(target, "base")
    base = base.rstrip("/")
    jobs = []
    for term in search_terms(target):
        for page in range(config.MAX_PAGES_PER_TERM):
            html = http.get(f"{base}/search/?q={quote(term)}&startrow={page * PAGE}").text
            found, total = parse_results(html, base)
            if not found and page == 0 and not jobs and "tr class=\"data-row" not in html:
                # No result table at all: a Career Site Builder page.
                return dedupe_raw(fetch_csb(target, http, base, html))
            jobs.extend(found)
            if not found or (page + 1) * PAGE >= total:
                break
    return dedupe_raw(jobs)
