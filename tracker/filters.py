"""Decide whether an offer is an internship we want to keep."""

from __future__ import annotations

import re
import unicodedata
from datetime import date

from . import config


_INTERNSHIP = [
    r"\bintern\b", r"\binterns\b", r"\binternships?\b",
    r"\bstages?\b", r"\bstagiaires?\b", r"\btraineeships?\b",
    r"\boff[\s-]?cycle\b",
    r"\bsummer (analyst|associate|intern|internship|program|programme|placement)s?\b",
    r"\bplacement year\b", r"\bindustrial placement\b",
    r"\bpraktik(um|ant|antin)\b", r"\bpraktika\b",
    r"\btirocini?o\b", r"\bstagista\b",
    r"\bpracticas\b", r"\bbecari[oa]s?\b",
    r"\bstagiair\b", r"\bstagelopen\b",
]

_EXCLUDED = [
    # Work-study / apprenticeships (alternance).
    r"\balternan(ce|t|te)\b", r"\bapprenti(e|s|ssage)?\b", r"\bapprenticeships?\b",
    r"\bcontrat (de )?professionnalisation\b", r"\bwork[\s-]?study\b",
    r"\bwerkstudent(in)?\b", r"\bworking student\b", r"\bduales? studium\b",
    r"\bdual study\b", r"\bausbildung\b",
    # Not internships in the usual sense.
    r"\bvolontariat international\b",
    r"\bspring (week|insight|program|programme|internship)\b", r"\binsight (day|week|program|programme)\b",
    r"\bhigh school\b", r"\blycee\b", r"\bcollege de 3e\b", r"\bstage (de )?(3e|troisieme|seconde)\b",
    r"\bstage d observation\b",
    # Senior roles that merely mention interns ("manage our interns").
    r"\b(head|director|manager) of (intern|stage)", r"\bintern(ship)? (coordinator|recruiter|manager)\b",
]

_INTERNSHIP_RE = [re.compile(p) for p in _INTERNSHIP]
_EXCLUDED_RE = [re.compile(p) for p in _EXCLUDED]
_YEAR_RE = re.compile(r"\b(20[2-3][0-9])\b")
# "VIE" (international volunteer contract) is matched case-sensitively so that
# "Assurance vie" (life insurance) is not excluded.
_VIE_RE = re.compile(r"\bV\.?I\.?E\b")


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9.\s-]+", " ", text.lower())


def looks_like_internship(title: str, employment_type: str = "") -> bool:
    t = _norm(title)
    if any(r.search(t) for r in _INTERNSHIP_RE):
        return True
    et = _norm(employment_type)
    return bool(et) and any(r.search(et) for r in _INTERNSHIP_RE)


def is_excluded(title: str, employment_type: str = "") -> bool:
    text = _norm(f"{title} {employment_type}")
    return bool(_VIE_RE.search(title or "")) or any(r.search(text) for r in _EXCLUDED_RE)


def out_of_window(title: str, today: date | None = None) -> bool:
    """True when every year in the title is outside config.year_window()
    (e.g. "Summer 2026" in October 2026, or "Summer 2031" with a 2029 graduation)."""
    first, last = config.year_window(today)
    years = [int(y) for y in _YEAR_RE.findall(title or "")]
    return bool(years) and not any(first <= y <= last for y in years)


def keep(title: str, employment_type: str = "", today: date | None = None) -> bool:
    return (
        looks_like_internship(title, employment_type)
        and not is_excluded(title, employment_type)
        and not out_of_window(title, today)
    )


# Phrases that, inside a job description, say the offer itself is an internship
# (as opposed to "we also run an internship programme"). Only used for
# employers flagged with `internship_in_description: true` in targets.yaml.
_DESCRIPTION_INTERNSHIP = re.compile(
    r"\b(this|our|the) (\d+[\s-]week |summer |off[\s-]cycle )?internship (is|will|runs|program|programme)\b"
    r"|\bas an intern\b|\binterns (will|work|spend|join)\b|\bduring (the|this|your) internship\b"
)


def description_says_internship(description: str) -> bool:
    return bool(_DESCRIPTION_INTERNSHIP.search(_norm(description)))


# Large corporates (type "corporate") post hundreds of finance internships
# (controlling, audit, accounting...). Only titles naming a markets activity
# are kept for them. "Pricing" alone is not enough there: it usually means
# product pricing (e.g. drug "market access and pricing").
_CORPORATE_MARKETS = re.compile(
    r"\btreasury\b|\btresorerie\b|\bcash management\b|\bhedg|\bcouverture|\bfx\b|\bforex\b|\bchange\b"
    r"|\bcurrenc|\bcommodit|\bmatieres premieres\b|\btrading\b|\btrader\b|\bmarket risk\b|\brisques? de marche\b"
    r"|\bsalle des marches\b|\bfront office\b|\bderivati|\bderives?\b|\bstructur|\bfinancement|\bfunding\b|\bfinancing\b"
    r"|\bcorporate finance\b|\bcapital markets\b|\bmarches de capitaux\b|\balm\b|\binvestor relations\b|\bm a\b"
)


def corporate_markets_role(title: str) -> bool:
    text = re.sub(r"\bchange management\b|\bconduite du changement\b", " ", _norm(title).replace("&", " "))
    return bool(_CORPORATE_MARKETS.search(text))
