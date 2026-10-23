"""Workable — public jobs widget API.

params:
  account: account name, as in apply.workable.com/<account>
"""

from .base import RawJob, iso_date, require
from ..geo import normalize_country


def fetch(target, http):
    (account,) = require(target, "account")
    data = http.get_json(f"https://apply.workable.com/api/v1/widget/accounts/{account}")
    jobs = []
    for item in data.get("jobs", []):
        locations = item.get("locations") or [item]
        names, countries = [], []
        for loc in locations:
            names.append(", ".join(filter(None, [loc.get("city"), loc.get("country")])))
            code = normalize_country(loc.get("countryCode") or loc.get("country", ""))
            if code:
                countries.append(code)
        jobs.append(RawJob(
            title=item.get("title", ""),
            url=item.get("url") or item.get("application_url") or f"https://apply.workable.com/{account}/j/{item.get('shortcode')}/",
            location="; ".join(filter(None, names)),
            native_id=item.get("shortcode", ""),
            posted_at=iso_date(item.get("published_on") or item.get("created_at")),
            countries=countries,
            employment_type=item.get("employment_type", "") or "",
        ))
    return jobs
