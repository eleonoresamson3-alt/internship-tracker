"""SmartRecruiters — public Posting API.

params:
  company: company identifier, as in jobs.smartrecruiters.com/<company>
"""

from urllib.parse import quote

from .base import RawJob, dedupe_raw, iso_date, require, search_terms
from .. import config
from ..geo import normalize_country

PAGE = 100


def fetch(target, http):
    (company,) = require(target, "company")
    jobs = []
    for term in search_terms(target):
        for page in range(config.MAX_PAGES_PER_TERM):
            url = (f"https://api.smartrecruiters.com/v1/companies/{company}/postings"
                   f"?limit={PAGE}&offset={page * PAGE}&q={quote(term)}")
            data = http.get_json(url)
            content = data.get("content", [])
            for item in content:
                loc = item.get("location") or {}
                location = loc.get("fullLocation") or ", ".join(
                    filter(None, [loc.get("city"), loc.get("region"), loc.get("country", "").upper()]))
                country = normalize_country(loc.get("country", ""))
                jobs.append(
                    RawJob(
                        title=item.get("name", ""),
                        url=f"https://jobs.smartrecruiters.com/{company}/{item.get('id')}",
                        location=location,
                        native_id=str(item.get("id", "")),
                        posted_at=iso_date(item.get("releasedDate")),
                        countries=[country] if country else [],
                        employment_type=" ".join(filter(None, [
                            (item.get("typeOfEmployment") or {}).get("label", ""),
                            (item.get("experienceLevel") or {}).get("label", ""),
                        ])),
                    )
                )
            if (page + 1) * PAGE >= data.get("totalFound", 0) or not content:
                break
    return dedupe_raw(jobs)
