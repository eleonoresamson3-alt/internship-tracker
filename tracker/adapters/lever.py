"""Lever postings — public JSON API.

params:
  site: company id, as in jobs.lever.co/<site>
  region: "eu" for boards hosted on jobs.eu.lever.co (optional)
"""

from .base import RawJob, iso_date, require
from ..geo import normalize_country


def fetch(target, http):
    (site,) = require(target, "site")
    host = "api.eu.lever.co" if target.params.get("region") == "eu" else "api.lever.co"
    data = http.get_json(f"https://{host}/v0/postings/{site}?mode=json")
    jobs = []
    for item in data:
        cats = item.get("categories") or {}
        locations = cats.get("allLocations") or [cats.get("location", "")]
        country = normalize_country(item.get("country", ""))
        jobs.append(
            RawJob(
                title=item.get("text", ""),
                url=item.get("hostedUrl", ""),
                location="; ".join(filter(None, locations)),
                native_id=item.get("id", ""),
                posted_at=iso_date(item.get("createdAt")),
                countries=[country] if country else [],
                employment_type=cats.get("commitment", "") or "",
                description=(item.get("descriptionPlain") or "")[:1000],
            )
        )
    return jobs
