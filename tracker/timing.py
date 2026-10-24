"""When does an internship start? Reads the title, then the description.

Produces a timing kind ("summer", "off-cycle" or "unknown"), the start year
(2027, 2028... when stated) and the start month when it can be found, e.g.
"Stage - Structuration - Juin 2027" or "Start date: January 2027".
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

MONTHS = {
    1: ["january", "jan", "janvier", "januar", "gennaio", "enero"],
    2: ["february", "feb", "fevrier", "februar", "febbraio", "febrero"],
    3: ["march", "mar", "mars", "marz", "maerz", "marzo"],
    4: ["april", "apr", "avril", "aprile", "abril"],
    5: ["may", "mai", "maggio", "mayo"],
    6: ["june", "jun", "juin", "juni", "giugno", "junio"],
    7: ["july", "jul", "juillet", "juli", "luglio", "julio"],
    8: ["august", "aug", "aout", "agosto"],
    9: ["september", "sept", "sep", "septembre", "settembre", "septiembre"],
    10: ["october", "oct", "octobre", "oktober", "ottobre", "octubre"],
    11: ["november", "nov", "novembre", "noviembre"],
    12: ["december", "dec", "decembre", "dezember", "dicembre", "diciembre"],
}
_MONTH_OF = {name: num for num, names in MONTHS.items() for name in names}
_MONTH_ALT = "|".join(sorted(_MONTH_OF, key=len, reverse=True))

# "January - June 2027", "Jan - Jun '27", "Jan/Feb 2027", "janvier a juin 2027": the
# internship STARTS with the first month of the range (it used to be read as June).
_RANGE = re.compile(
    rf"\b(?P<m1>{_MONTH_ALT})\.?\s*(?:-|/|to|a|au|bis|al|till|until|through)\s*(?P<m2>{_MONTH_ALT})\.?\s*"
    rf"(?P<y>20\d\d|2[4-9]|3[0-5])\b"
)
_RANGE_CONTEXT = re.compile(r"\b(internship|stage|praktikum|period\w*|duration|duree|dates?|from|de|du|vom|dal|start\w*|"
                            r"debut\w*|placement|programme|program)\b[^.]*$")
# In a description, "June 2027" counts only right after a start / period word
# ("starting in", "available from", "internship period", "duree du stage"...).
_MONTH_CONTEXT = re.compile(r"\b(start\w*|commenc\w*|debut\w*|intake|available|disponib\w*|period\w*|duration|duree|"
                            r"beginning|a partir|from|des le|ab|beginn\w*|inizio|inicio)\b[^.]{0,85}$")   # long enough for "x ou y ou z"
# "Start date: 2027-04-01", "start date: 15/04/2027" (day/month order only when unambiguous)
_START_ISO = re.compile(r"\b(start\w*|debut\w*|commenc\w*)( date)?\s*[:\-]?\s*(?P<y>20\d\d)-(?P<m>\d\d)-\d\d\b")
_START_DMY = re.compile(r"\b(start\w*|debut\w*|commenc\w*)( date)?\s*[:\-]?\s*(?P<a>\d{1,2})/(?P<b>\d{1,2})/(?P<y>20\d\d)\b")
# "Feb2027" -> "Feb 2027"
_GLUED = re.compile(rf"\b({_MONTH_ALT})(20\d\d)\b")
# "June 2027", "juin 2027", "06/2027"
_MONTH_YEAR = re.compile(rf"\b(?P<m>{_MONTH_ALT})\.?\s+(?P<y>20\d\d)\b|\b(?P<mm>0?[1-9]|1[0-2])\s*/\s*(?P<y2>20\d\d)\b")
# "start date: June", "starting in September 2027", "a partir de janvier", "debut : mars 2027"
_START = re.compile(
    rf"\b(start\w*( date)?( in| from| on)?|commenc\w*( en| in| le)?|beginning( in)?|debut\w*( du stage)?( prevu)?( en| le)?|"
    rf"a partir d[eu]|des|disponible( a partir)? d[eu]|ab|beginn( im| am)?|inizio|inicio)\s*[:\-]?\s*"
    rf"(le |en |el |im |in )?(\d{{1,2}}(er)? )?(?P<m>{_MONTH_ALT})\b\.?(\s+(?P<y>20\d\d))?"
)
# Vague periods: "début 2027", "early 2027", "Q1 2027", "spring 2027", "fall 2027"...
# mapped to the first month they can mean.
_PERIODS = [
    (r"(early|debut|beginning of|start of|anfang|inizio|principios de)", 1),
    (r"(q1|h1|first quarter|first half|1er trimestre|premier trimestre|premier semestre)", 1),
    (r"(winter quarter|winter|hiver|invierno)", 1),
    (r"(spring|printemps|fruhjahr|fruehjahr|primavera)", 3),
    (r"(q2|second quarter)", 4),
    (r"(autumn|fall|automne|herbst|otono)", 9),
    (r"(q4|end of|fin|late|ende)", 10),
]
_PERIOD_RE = [(re.compile(rf"\b{words} (?P<y>20\d\d)\b"), month) for words, month in _PERIODS]
_PERIOD_START_RE = [(re.compile(rf"\b(start\w*|commenc\w*|debut\w*)( in| en| du stage)?( the)? {words} (?P<y>20\d\d)\b"), month)
                    for words, month in _PERIODS]
# "estate" (Italian summer) only with a year: alone it is mostly "real estate".
_SUMMER = re.compile(r"\bsummer\b|\bete 20\d\d\b|\bstage d ete\b|\bsommer(praktikum)?\b|\bestate 20\d\d\b|\bstage estivo\b|\bverano\b")
_OFF_CYCLE = re.compile(r"\boff[\s-]?cycle\b")
_YEAR = re.compile(r"\b(20[2-3]\d)\b")
_SIX_MONTHS = re.compile(r"\b6[\s-]?(months?|mois|monate)\b|\bsix months\b|\bsix mois\b")


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9/:\-]+", " ", text.lower())


@dataclass
class Timing:
    kind: str           # "summer" | "off-cycle" | "unknown"
    year: int | None    # start year when stated
    month: int | None   # start month when stated
    six_months: bool

    @property
    def start(self) -> str:
        """YYYY-MM, YYYY or "" depending on what is known."""
        if self.year and self.month:
            return f"{self.year}-{self.month:02d}"
        return str(self.year) if self.year else ""


def _start_month(text: str, strict: bool = False):
    """strict=True (descriptions) only trusts explicit "start ..." phrases, since
    a description also mentions other dates (deadlines, interviews...)."""
    if not strict:
        match = _RANGE.search(text)
        if match:
            year = int(match.group("y"))
            return _MONTH_OF[match.group("m1")], year if year > 2000 else 2000 + year
    else:
        # In a description every explicit start found counts, and the LATEST one wins:
        # "start dates: January to June 2027, July to December 2027" offers a July start,
        # so the offer must not be dropped as starting in January (in doubt, keep).
        found = []
        # A range counts only when introduced as the internship period
        # ("internship period: April - September 2027", "du stage : de avril a septembre 2027").
        ranges = list(_RANGE.finditer(text))
        for match in ranges:
            if _RANGE_CONTEXT.search(text[max(0, match.start() - 60):match.start()]):
                year = int(match.group("y"))
                found.append((year if year > 2000 else 2000 + year, _MONTH_OF[match.group("m1")]))
        inside_range = lambda pos: any(r.start() <= pos < r.end() for r in ranges)   # "... to June 2027" is an end
        for match in _MONTH_YEAR.finditer(text):
            if match.group("m") and not inside_range(match.start()) \
                    and _MONTH_CONTEXT.search(text[max(0, match.start() - 100):match.start()]):
                found.append((int(match.group("y")), _MONTH_OF[match.group("m")]))
        for match in _START_ISO.finditer(text):
            if 1 <= int(match.group("m")) <= 12:
                found.append((int(match.group("y")), int(match.group("m"))))
        for match in _START_DMY.finditer(text):
            a, b = int(match.group("a")), int(match.group("b"))
            if a > 12 and 1 <= b <= 12:      # 15/04/2027: day first, month = 4
                found.append((int(match.group("y")), b))
            elif b > 12 and 1 <= a <= 12:    # 04/15/2027: month first
                found.append((int(match.group("y")), a))
            # 01/04/2027 is ambiguous (1 April or 4 January): left unknown.
        if found:
            year, month = max(found)
            return month, year
    match = None if strict else _MONTH_YEAR.search(text)
    if match:
        if match.group("m"):
            return _MONTH_OF[match.group("m")], int(match.group("y"))
        return int(match.group("mm")), int(match.group("y2"))
    match = _START.search(text)
    if match:
        year = match.group("y")
        return _MONTH_OF[match.group("m")], int(year) if year else None
    # Vague periods: anywhere in a title, only after "start ..." in a description.
    for pattern, month in (_PERIOD_START_RE if strict else _PERIOD_RE):
        match = pattern.search(text)
        if match:
            return month, int(match.group("y"))
    return None, None


def analyse(title: str, description: str = "") -> Timing:
    t, d = _GLUED.sub(r"\1 \2", _norm(title)), _GLUED.sub(r"\1 \2", _norm(description[:16000]))
    month, year = _start_month(t)
    if month is None and d:
        month, year = _start_month(d, strict=True)
    if year is None:
        years = [int(y) for y in _YEAR.findall(t)]
        year = min(years) if years else None

    if _SUMMER.search(t) or (month in (5, 6, 7) and not _OFF_CYCLE.search(t)):
        kind = "summer"
    elif _OFF_CYCLE.search(t) or month is not None or _OFF_CYCLE.search(d):
        kind = "off-cycle"
    elif _SUMMER.search(d):
        kind = "summer"
    else:
        kind = "unknown"
    return Timing(kind=kind, year=year, month=month, six_months=bool(_SIX_MONTHS.search(f"{t} {d}")))
