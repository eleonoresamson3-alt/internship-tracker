"""Oracle Recruiting Cloud (Oracle HCM "Candidate Experience") — public REST API.

params:
  host: e.g. jpmc.fa.oraclecloud.com
  site: site number, e.g. CX_1001 (visible in /hcmUI/CandidateExperience/en/sites/<site>/)
"""

from urllib.parse import quote

from .base import RawJob, dedupe_raw, iso_date, require, search_terms
from .. import config
from ..geo import normalize_country

PAGE = 25


def fetch(target, http):
    host, site = require(target, "host", "site")
    lang = target.params.get("lang", "en")
    jobs = []
    for term in search_terms(target):
        for page in range(config.MAX_PAGES_PER_TERM):
            finder = (f"findReqs;siteNumber={site},limit={PAGE},offset={page * PAGE},"
                      f"keyword=\"{term}\",sortBy=POSTING_DATES_DESC")
            url = (f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
                   f"?onlyData=true&expand=requisitionList.secondaryLocations&finder={quote(finder, safe='=;,')}")
            data = http.get_json(url)
            block = (data.get("items") or [{}])[0]
            reqs = block.get("requisitionList", []) or []
            for req in reqs:
                secondary = [s.get("Name", "") for s in req.get("secondaryLocations", []) or []]
                country = normalize_country(req.get("PrimaryLocationCountry", ""))
                jobs.append(
                    RawJob(
                        title=req.get("Title", ""),
                        url=f"https://{host}/hcmUI/CandidateExperience/{lang}/sites/{site}/job/{req.get('Id')}",
                        location="; ".join(filter(None, [req.get("PrimaryLocation", "")] + secondary)),
                        native_id=str(req.get("Id", "")),
                        posted_at=iso_date(req.get("PostedDate")),
                        countries=[country] if country else [],
                        employment_type=req.get("JobSchedule", "") or "",
                        description=(req.get("ShortDescriptionStr") or "")[:1000],
                    )
                )
            total = block.get("TotalJobsCount", 0) or 0
            if not reqs or (page + 1) * PAGE >= total:
                break
    return dedupe_raw(jobs)
