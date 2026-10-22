"""Recruitee — public offers API.

params:
  company: subdomain, as in <company>.recruitee.com
"""

from .base import RawJob, iso_date, require
from ..geo import normalize_country


def fetch(target, http):
    (company,) = require(target, "company")
    data = http.get_json(f"https://{company}.recruitee.com/api/offers/")
    jobs = []
    for item in data.get("offers", []):
        country = normalize_country(item.get("country_code") or item.get("country", ""))
        jobs.append(RawJob(
            title=item.get("title", ""),
            url=item.get("careers_url", ""),
            location=item.get("location", "") or ", ".join(filter(None, [item.get("city"), item.get("country")])),
            native_id=str(item.get("id", "")),
            posted_at=iso_date(item.get("published_at") or item.get("created_at")),
            countries=[country] if country else [],
            employment_type=item.get("employment_type_code", "") or "",
        ))
    return jobs
