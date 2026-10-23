"""Monetary policy meeting dates of the ECB and the Fed, from their official pages.

If a page cannot be read or parsed, the manual list of news_sources.yaml
(calendar_manual) is used for that bank instead. Dates are never guessed.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

from bs4 import BeautifulSoup

from ..http import PoliteClient

ECB_URL = "https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html"
FED_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}


def parse_ecb(html: str) -> list[dict]:
    """Monetary policy meetings (one or two days) from the ECB calendar page."""
    soup = BeautifulSoup(html, "html.parser")
    days = []
    for dt in soup.find_all("dt"):
        dd = dt.find_next_sibling("dd")
        m = re.search(r"(\d{2})/(\d{2})/(\d{4})", dt.get_text())
        if not dd or not m:
            continue
        text = dd.get_text(" ", strip=True).lower()
        if "monetary policy meeting" in text and "non-monetary" not in text:
            days.append(date(int(m[3]), int(m[2]), int(m[1])))
    meetings = []
    for d in sorted(set(days)):
        if meetings and d - meetings[-1]["_end"] <= timedelta(days=1):
            meetings[-1]["_end"] = d
        else:
            meetings.append({"_start": d, "_end": d})
    return [{"bank": "BCE", "date": m["_start"].isoformat(), "end": m["_end"].isoformat(),
             "note": "décision et conférence de presse le dernier jour", "source": "official", "source_url": ECB_URL}
            for m in meetings]


def parse_fed(html: str) -> list[dict]:
    """FOMC meetings from the Fed calendar page (one panel per year)."""
    soup = BeautifulSoup(html, "html.parser")
    meetings = []
    for panel in soup.select(".panel"):
        heading = panel.find(["h4", "h3"])
        y = re.search(r"(\d{4}) FOMC Meetings", heading.get_text()) if heading else None
        if not y:
            continue
        year = int(y[1])
        for row in panel.select(".fomc-meeting"):
            month_el = row.select_one(".fomc-meeting__month")
            date_el = row.select_one(".fomc-meeting__date")
            if not month_el or not date_el:
                continue
            months = [MONTHS.get(p.strip().lower()[:3]) for p in month_el.get_text().split("/")]
            dm = re.fullmatch(r"(\d{1,2})(?:-(\d{1,2}))?(\*?)", date_el.get_text(strip=True))
            if not dm or None in months:
                continue  # unscheduled meetings, notation votes, cancelled...
            first, last = int(dm[1]), int(dm[2] or dm[1])
            start = date(year, months[0], first)
            end = date(year, months[-1], last)
            meetings.append({"bank": "Fed", "date": start.isoformat(), "end": end.isoformat(),
                             "note": "avec projections économiques (SEP)" if dm[3] else "",
                             "source": "official", "source_url": FED_URL})
    return sorted(meetings, key=lambda m: m["date"])


def fetch_all(manual: list[dict], http: PoliteClient) -> tuple[list[dict], list[dict]]:
    """All meetings, official first, manual list as fallback per bank. Returns (meetings, errors)."""
    meetings, errors = [], []
    for bank, url, parser in (("BCE", ECB_URL, parse_ecb), ("Fed", FED_URL, parse_fed)):
        try:
            found = parser(http.get(url).text)
            if not found:
                raise ValueError("no meeting found (page layout changed?)")
            meetings.extend(found)
        except Exception as exc:
            errors.append({"source": f"Calendrier {bank}", "url": url, "error": f"{type(exc).__name__}: {exc}"[:300]})
            meetings.extend({"bank": bank, "date": str(m["date"]), "end": str(m.get("end", m["date"])),
                             "note": m.get("note", ""), "source": "manual", "source_url": url}
                            for m in manual if m.get("bank") == bank)
    return sorted(meetings, key=lambda m: (m["date"], m["bank"])), errors
