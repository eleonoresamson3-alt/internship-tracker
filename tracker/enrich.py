"""Find the start date of offers whose title does not give it, by reading the ad page.

Many titles only say "Off-cycle Internship 2027" or nothing at all, while the
ad itself says "start date: April 2027". For each kept offer without a start
month, the ad page is fetched once (politely, robots.txt respected) and its
text is read with the strict description rules of tracker/timing.py: only an
explicit start phrase counts ("start date: ...", "available from ...",
"internship period: April - September 2027"). If nothing explicit is found the
offer is kept as it is. In doubt, an offer is never removed.

Results are cached in data/start_dates.json (public information only), so an
ad is read once, not every day.
"""

from __future__ import annotations

import json
import logging
import re
import threading
from urllib.parse import urlsplit
from datetime import date, timedelta

from bs4 import BeautifulSoup

from . import config, store
from .http import PoliteClient
from .sanitize import clean_text

log = logging.getLogger(__name__)

CACHE_FILE = config.DATA_DIR / "start_dates.json"
MAX_PAGES_PER_RUN = 400      # first run reads the backlog; later runs only new offers
RETRY_AFTER_DAYS = 7         # a page that could not be read is tried again after a week
MAX_TEXT = 15000


class StartDateCache:
    def __init__(self, path=CACHE_FILE):
        self.path = path
        self.entries: dict = store.load_json(path, {}).get("offers", {})
        self.lock = threading.Lock()
        self.fetched = 0

    def get(self, job_id: str):
        with self.lock:
            return self.entries.get(job_id)

    def put(self, job_id: str, entry: dict) -> None:
        with self.lock:
            self.entries[job_id] = entry

    def take_budget(self) -> bool:
        with self.lock:
            if self.fetched >= MAX_PAGES_PER_RUN:
                return False
            self.fetched += 1
            return True

    def save(self, keep_ids: set[str]) -> None:
        # Offers that left the history are forgotten.
        entries = {k: v for k, v in self.entries.items() if k in keep_ids}
        store.save_json(self.path, {"offers": entries})


def page_text(html: str) -> str:
    """Ad text: schema.org JobPosting first (with jobStartDate when given), else the visible text."""
    soup = BeautifulSoup(html, "html.parser")
    parts = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (ValueError, TypeError):
            continue
        for node in data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []:
            if isinstance(node, dict) and node.get("@type") == "JobPosting":
                if node.get("jobStartDate"):
                    parts.append(f"Start date: {str(node['jobStartDate'])[:10]}.")
                parts.append(clean_text(node.get("description") or "", MAX_TEXT))   # also escaped HTML
    if not parts:
        for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
            tag.decompose()
        parts.append(soup.get_text(" "))
    return " ".join(" ".join(parts).split())[:MAX_TEXT]


_ORACLE_AD = re.compile(r"^https://(?P<host>[^/]+\.oraclecloud\.com)/hcmUI/CandidateExperience/[^/]+/sites/(?P<site>[^/]+)/job/(?P<id>\d+)")


def read_ad(url: str, http: PoliteClient) -> str:
    """Text of one ad. Oracle pages are rendered in JavaScript: their public REST API gives the text."""
    m = _ORACLE_AD.match(url)
    if m:
        api = (f"https://{m['host']}/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails"
               f"?expand=all&onlyData=true&finder=ById;Id=%22{m['id']}%22,siteNumber={m['site']}")
        item = (http.get_json(api, retries=1).get("items") or [{}])[0]
        html = " ".join(str(item.get(k) or "") for k in (
            "ExternalDescriptionStr", "ExternalResponsibilitiesStr", "ExternalQualificationsStr",
            "CorporateDescriptionStr", "ShortDescriptionStr"))
        return clean_text(html, MAX_TEXT)
    return page_text(http.get(url, retries=1).text)


def lookup(job_id: str, url: str, http: PoliteClient, cache: StartDateCache, today: date) -> str | None:
    """Ad text to analyse for this offer, or None (unknown, not readable, or budget used)."""
    if urlsplit(url).netloc.endswith("myworkdayjobs.com"):
        return None   # the Workday adapter already reads each ad's full text through its API
    entry = cache.get(job_id)
    if entry and entry.get("text") is not None:
        return entry["text"]
    if entry and entry.get("error") and date.fromisoformat(entry["checked"]) > today - timedelta(days=RETRY_AFTER_DAYS):
        return None
    if not cache.take_budget():
        return None
    try:
        text = read_ad(url, http)
    except Exception as exc:  # unreadable ad: keep the offer, try again later
        cache.put(job_id, {"checked": today.isoformat(), "error": f"{type(exc).__name__}"[:80]})
        return None
    # Only the sentences that can carry a start date are kept in the cache.
    cache.put(job_id, {"checked": today.isoformat(), "text": _relevant(text)})
    return _relevant(text)


def _relevant(text: str) -> str:
    """Sentences mentioning a start, a period or a duration (keeps the cache small)."""
    keys = ("start", "commenc", "début", "debut", "period", "périod", "duration", "durée", "duree", "available",
            "disponib", "intake", "from", "à partir", "a partir", "ab ", "beginn", "inizio", "inicio", "deadline",
            "apply by", "closing", "date limite", "candidature")
    sentences = [s.strip() for s in text.replace("\n", " ").split(".")]
    return ". ".join(s for s in sentences if any(k in s.lower() for k in keys))[:3000]
