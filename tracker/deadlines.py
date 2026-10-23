"""Application deadlines: stated in the ad when possible, estimated otherwise.

- parse(): reads an explicit deadline in the description ("Application
  deadline: 15 November 2026", "date limite de candidature : 30/11/2026"...).
- estimate(): when the ad gives none, the usual closing month of the
  recruiting cycle for this kind of employer (end of that month).
The site shows which of the two a date comes from.
"""

from __future__ import annotations

import calendar
import re
import unicodedata
from datetime import date

from . import config
from .timing import MONTHS, Timing

_MONTH_OF = {name: num for num, names in MONTHS.items() for name in names}
_MONTH_ALT = "|".join(sorted(_MONTH_OF, key=len, reverse=True))

_LEAD = (
    r"(application deadline|deadline( for applications)?|closing date|applications? (close|closes|closing)( on)?"
    r"|apply by|apply before|date limite( de (candidature|depot))?|candidatures? (jusqu au|avant le)"
    r"|postuler avant le|clotur\w* (le|des candidatures)?|bewerbungsschluss|bewerbungsfrist|scadenza|fecha limite)"
)
_SEP = r"\s*(:|-|is|est|le|on|by|au)?\s*(le |the )?"
_DAY_MONTH_YEAR = rf"(?P<d>\d{{1,2}})(st|nd|rd|th|er)?\s+(?P<m>{_MONTH_ALT})\.?,?\s+(?P<y>20\d\d)"
_MONTH_DAY_YEAR = rf"(?P<m2>{_MONTH_ALT})\.?\s+(?P<d2>\d{{1,2}})(st|nd|rd|th)?,?\s+(?P<y2>20\d\d)"
_NUMERIC = r"(?P<d3>\d{1,2})[/.](?P<m3>\d{1,2})[/.](?P<y3>20\d\d)"
_ISO = r"(?P<y4>20\d\d)-(?P<m4>\d{2})-(?P<d4>\d{2})"
_DEADLINE = re.compile(rf"\b{_LEAD}{_SEP}({_DAY_MONTH_YEAR}|{_MONTH_DAY_YEAR}|{_NUMERIC}|{_ISO})")


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9/.:\-,]+", " ", text.lower())


def parse(text: str) -> date | None:
    """Explicit deadline stated in the ad, if any."""
    match = _DEADLINE.search(_norm(text[:6000]))
    if not match:
        return None
    g = match.groupdict()
    try:
        if g["d"]:
            return date(int(g["y"]), _MONTH_OF[g["m"]], int(g["d"]))
        if g["d2"]:
            return date(int(g["y2"]), _MONTH_OF[g["m2"]], int(g["d2"]))
        if g["d3"]:  # European order: day/month/year
            return date(int(g["y3"]), int(g["m3"]), int(g["d3"]))
        return date(int(g["y4"]), int(g["m4"]), int(g["d4"]))
    except ValueError:
        return None


# Usual application windows per kind of employer, relative to the start year Y
# of the internship: (start month, close year offset, close month).
# Keep in sync with CYCLES in docs/app.js (windows shown in the Entreprises tab).
CYCLES = {
    "anglo": [(6, -1, 11), (7, 0, 4), (1, -1, 11)],
    "trading": [(6, -1, 10), (7, 0, 4), (1, -1, 12)],
    "fr": [(6, 0, 4), (9, 0, 7), (1, -1, 11)],
    "consulting": [(6, 0, 3), (1, -1, 10)],
}
TYPE_CYCLE = {
    "intl_bank": "anglo", "infrastructure": "anglo", "hedge_fund": "trading",
    "french_bank": "fr", "european_bank": "fr", "broker": "fr", "asset_manager": "fr",
    "insurance": "fr", "commodities": "fr", "software": "fr", "corporate": "fr",
    "consulting": "consulting",
}


def estimate(employer_type: str, when: Timing, today: date | None = None) -> date | None:
    """Usual closing date for this offer, or None when it cannot be estimated
    (institutions, or the usual window is already over: rolling recruitment)."""
    today = today or date.today()
    cycle = CYCLES.get(TYPE_CYCLE.get(employer_type, ""))
    if not cycle:
        return None
    if when.month:
        target_month = when.month
    elif when.kind == "summer" or when.kind == "unknown":
        target_month = 6
    else:  # off-cycle without a month: the next off-cycle start
        target_month = 7
    # Window whose start month is the closest to the offer's start month.
    start_month, close_offset, close_month = min(cycle, key=lambda w: abs(w[0] - target_month))
    year = when.year or max(config.EARLIEST_START[0], today.year)
    close_year = year + close_offset
    closing = date(close_year, close_month, calendar.monthrange(close_year, close_month)[1])
    return closing if closing >= today else None
