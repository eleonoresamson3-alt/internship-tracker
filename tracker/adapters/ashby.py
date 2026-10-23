"""Ashby job boards — public posting API.

params:
  board: job board name, as in jobs.ashbyhq.com/<board>
"""

from .base import RawJob, iso_date, require
from ..geo import normalize_country


def fetch(target, http):
    (board,) = require(target, "board")
    data = http.get_json(f"https://api.ashbyhq.com/posting-api/job-board/{board}")
    jobs = []
    for item in data.get("jobs", []):
        locations = [item.get("location", "")] + [
            s.get("location", "") for s in item.get("secondaryLocations", []) or []]
        address = ((item.get("address") or {}).get("postalAddress") or {})
        country = normalize_country(address.get("addressCountry", ""))
        jobs.append(
            RawJob(
                title=item.get("title", ""),
                url=item.get("jobUrl", ""),
                location="; ".join(filter(None, locations)),
                native_id=item.get("id", "") or item.get("jobUrl", ""),
                posted_at=iso_date(item.get("publishedAt")),
                countries=[country] if country else [],
                employment_type=item.get("employmentType", "") or "",
            )
        )
    return jobs
