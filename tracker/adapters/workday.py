"""Workday career sites — the JSON endpoints used by the public job search page.

params:
  url: public site URL, e.g. https://ms.wd5.myworkdayjobs.com/External
       (tenant and site are derived from it; a locale segment like /en-US is ignored)
  tenant / site: optional overrides when the URL does not follow the usual pattern
"""

import html
import re
from urllib.parse import urlsplit

from .base import AdapterError, RawJob, dedupe_raw, require, search_terms, title_may_match
from .. import config
from ..geo import normalize_country

PAGE = 20
_LOCALE = re.compile(r"^[a-z]{2}-[A-Z]{2}$")


def parse_site_url(url: str) -> tuple[str, str, str]:
    parts = urlsplit(url)
    host = parts.netloc
    tenant = host.split(".")[0]
    segments = [s for s in parts.path.split("/") if s and not _LOCALE.match(s)]
    if not segments:
        raise AdapterError(f"cannot find the Workday site name in {url}")
    return host, tenant, segments[0]


def fetch(target, http):
    (url,) = require(target, "url")
    host, tenant, site = parse_site_url(url)
    tenant = target.params.get("tenant", tenant)
    site = target.params.get("site", site)
    api = f"https://{host}/wday/cxs/{tenant}/{site}"

    postings = {}
    for term in search_terms(target):
        for page in range(config.MAX_PAGES_PER_TERM):
            data = http.post_json(f"{api}/jobs", {
                "appliedFacets": {}, "limit": PAGE, "offset": page * PAGE, "searchText": term})
            items = data.get("jobPostings", [])
            for item in items:
                path = item.get("externalPath")
                if path and title_may_match(item.get("title", "")):
                    postings.setdefault(path, item)
            if not items or (page + 1) * PAGE >= data.get("total", 0):
                break

    jobs = []
    for path, item in postings.items():
        location = item.get("locationsText", "")
        countries = []
        posted = ""
        # Only offers that pass the title filter get a detail call, to resolve
        # "3 Locations" into real places and to get the country.
        try:
            detail = http.get_json(f"{api}{path}").get("jobPostingInfo", {})
            locs = [detail.get("location", "")] + list(detail.get("additionalLocations", []) or [])
            location = "; ".join(filter(None, locs)) or location
            country = normalize_country((detail.get("country") or {}).get("descriptor", ""))
            countries = [country] if country else []
            posted = detail.get("startDate", "") or ""
            native_id = detail.get("jobReqId") or path
            description = re.sub(r"<[^>]+>", " ", html.unescape(detail.get("jobDescription", "") or ""))[:4000]
        except Exception:
            native_id, description = path, ""
        jobs.append(
            RawJob(
                title=item.get("title", ""),
                url=f"https://{host}/{site}{path}",
                location=location,
                native_id=str(native_id),
                posted_at=posted[:10],
                countries=countries,
                description=" ".join(description.split()),
            )
        )
    return dedupe_raw(jobs)
