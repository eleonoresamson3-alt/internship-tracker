"""Greenhouse job boards — public JSON API.

params:
  board: board token, as in job-boards.greenhouse.io/<board>
"""

from .base import RawJob, iso_date, require


def fetch(target, http):
    (board,) = require(target, "board")
    # content=true adds departments, which is where some firms flag internships
    # (titles like "Quantitative Trader" with department "Internships").
    data = http.get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true")
    jobs = []
    for item in data.get("jobs", []):
        location = (item.get("location") or {}).get("name", "")
        offices = [o.get("location") or o.get("name", "") for o in item.get("offices", []) or []]
        jobs.append(
            RawJob(
                title=item.get("title", ""),
                url=item.get("absolute_url", ""),
                location="; ".join(filter(None, [location] + [o for o in offices if o and o != location])),
                native_id=str(item.get("id", "")),
                posted_at=iso_date(item.get("first_published") or item.get("updated_at")),
                employment_type=" ".join(d.get("name", "") for d in item.get("departments", []) or []),
            )
        )
    return jobs
