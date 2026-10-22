"""Career sites whose search runs on Algolia (e.g. Société Générale).

The page's own script calls algoliasearch("<app id>", "<public search key>").
The adapter reads that script at run time to get the same public, read-only
search key the browser uses (it is never stored in this repository), then
queries the index like the page does.

params:
  script_url: URL of the page script containing algoliasearch("APP", "KEY")
  index: index name, e.g. prod_jobs_en
  base: site root used to build offer URLs from relative paths
"""

import json
import re
from urllib.parse import urlencode, urljoin

from .base import AdapterError, RawJob, dedupe_raw, iso_date, require, search_terms
from .. import config
from ..geo import normalize_country

PAGE = 100
_KEYS = re.compile(r"""algoliasearch\(\s*["'](\w+)["']\s*,\s*["'](\w+)["']""")


def _first(hit: dict, *names: str) -> str:
    for name in names:
        value = hit.get(name)
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value if v)
        if value:
            return str(value)
    return ""


def fetch(target, http):
    script_url, index, base = require(target, "script_url", "index", "base")
    match = _KEYS.search(http.get(script_url).text)
    if not match:
        raise AdapterError("algoliasearch(...) call not found in the page script")
    app_id, key = match.groups()
    headers = {"X-Algolia-Application-Id": app_id, "X-Algolia-API-Key": key}
    # Algolia serves the same index from several hosts; use the first that answers.
    hosts = [f"{app_id.lower()}-dsn.algolia.net", f"{app_id.lower()}.algolia.net",
             f"{app_id.lower()}-1.algolianet.com", f"{app_id.lower()}-2.algolianet.com"]
    url, last_error = None, None
    for host in hosts:
        try:
            http.post_json(f"https://{host}/1/indexes/{index}/query", {"params": "query=&hitsPerPage=1"},
                           headers=headers, retries=0)
            url = f"https://{host}/1/indexes/{index}/query"
            break
        except Exception as exc:
            last_error = exc
    if url is None:
        raise AdapterError(f"no Algolia host reachable: {last_error}")
    jobs = []
    for term in search_terms(target):
        for page in range(config.MAX_PAGES_PER_TERM):
            data = http.post_json(url, {"params": urlencode({"query": term, "hitsPerPage": PAGE, "page": page})},
                                  headers=headers)
            for hit in data.get("hits", []):
                path = _first(hit, "url", "path", "link", "alias")
                city = _first(hit, "city", "location", "jobLocation")
                country = _first(hit, "country", "countryName")
                code = normalize_country(country)
                jobs.append(RawJob(
                    title=_first(hit, "title", "jobTitle", "name", "label"),
                    url=urljoin(base, path) if path else "",
                    location=", ".join(filter(None, [city, country])),
                    native_id=str(hit.get("objectID", "")),
                    posted_at=iso_date(_first(hit, "date", "publicationDate", "created")),
                    countries=[code] if code else [],
                    employment_type=_first(hit, "contract", "contractType", "jobType", "type"),
                ))
            if page + 1 >= (data.get("nbPages") or 0):
                break
    jobs = dedupe_raw(jobs)
    if jobs and not any(j.title for j in jobs):
        sample = json.dumps(data.get("hits", [{}])[:1])[:300]
        raise AdapterError(f"unexpected Algolia hit format: {sample}")
    return jobs
