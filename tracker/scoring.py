"""Relevance score: role first, then geography, then timing."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from . import geo

# (pattern, role family). Patterns are matched on a lower-case, accent-free text.
HIGH = [
    (r"\bstructur(ing|er|ers|ation|eur|euse)\b", "Structuring"),
    (r"\bstructured (products?|solutions|finance)\b|\bproduits structures\b", "Structuring"),
    (r"\bfinancial engineer(ing)?\b|\bingenierie financiere\b", "Structuring"),
    (r"\bpricing\b", "Pricing / Quant"),
    (r"\bquant(itative)? analyst\b", "Pricing / Quant"),
    (r"\bquant(itative)? research(er)?\b", "Pricing / Quant"),
    (r"\bquant(itative)? (analysis|modell?ing|finance)\b", "Pricing / Quant"),
    (r"\bfinancial modell?ing\b", "Pricing / Quant"),
    (r"\bmodelisation financiere\b", "Pricing / Quant"),
    (r"\bderivati(ves?|fs?)\b", "Pricing / Quant"),
    (r"\bderives?\b", "Pricing / Quant"),
    (r"\bmodel (validation|risk)\b", "Risk"),
    (r"\bvalidation (des |de )?modeles?\b", "Risk"),
    (r"\bxva\b|\bcva\b", "Risk"),
    (r"\b(risque|risques) de marche\b", "Risk"),
    (r"\bmarket risk\b", "Risk"),
    (r"\bmarktrisiko\b", "Risk"),
]

MEDIUM = [
    (r"\bquant(itative)? dev(eloper)?\b", "Quant dev"),
    (r"\bstrats?\b", "Quant dev"),
    (r"\btrad(ing|er|ers)\b", "Trading"),
    (r"\bproduct control\b|\bcontrole produits?\b", "Product control"),
    (r"\bquant(s|itative)?\b", "Pricing / Quant"),
]

LOW = [
    (r"\bmarkets?\b|\bmarches\b|\bmarche\b", "Markets (other)"),
    (r"\bsales\b|\bvente\b", "Markets (other)"),
    (r"\bfixed income\b|\brates\b|\btaux\b|\bcredit\b|\bfx\b|\bforex\b|\bchange\b", "Markets (other)"),
    (r"\bequit(y|ies)\b|\bactions\b|\bcommodit(y|ies)\b|\bmatieres premieres\b", "Markets (other)"),
    (r"\bglobal markets\b|\bcib\b|\binvestment bank(ing)?\b|\bbanque d investissement\b", "Markets (other)"),
    (r"\brisk\b|\brisque\b|\brisques\b|\balm\b|\btreasury\b|\btresorerie\b", "Risk"),
    (r"\bportfolio\b|\bportefeuille\b|\basset management\b|\bgestion d actifs\b|\binvestment\b", "Markets (other)"),
    (r"\bresearch\b|\brecherche\b|\beconomist\b|\bdata scien(ce|tist)\b", "Markets (other)"),
    (r"\bfinance\b|\bfinancial\b|\bfinanciere?\b", "Markets (other)"),
]

ROLE_POINTS = {"high": 50, "medium": 30, "low": 10}

GEO_POINTS = {
    "France": 30,
    "Europe (priority)": 20,
    "Europe (other)": 12,
    "Rest of world": 0,
}
CITY_BONUS = {"paris": 5, "london": 5, "la defense": 5}

TIMING = [
    (r"\boff[\s-]?cycle\b", 10),
    (r"\b6[\s-]?(months?|mois)\b|\bsix months\b", 10),
    (r"\b2027\b", 5),
]

_COMPILED = {
    level: [(re.compile(p), fam) for p, fam in rules]
    for level, rules in (("high", HIGH), ("medium", MEDIUM), ("low", LOW))
}
_TIMING = [(re.compile(p), pts) for p, pts in TIMING]


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.lower())


@dataclass
class Score:
    total: int
    role_level: str      # "high" | "medium" | "low" | "none"
    family: str          # role family shown in the interface
    region: str          # best region among the offer's countries
    breakdown: dict


def role_match(title: str) -> tuple[str, str]:
    """Return (level, family) for the best role signal found in the title.

    Descriptions are deliberately ignored: at trading firms every ad mentions
    "trading", which would push unrelated roles (IT, HR...) into the list.
    """
    t = _norm(title)
    for level in ("high", "medium", "low"):
        for pattern, family in _COMPILED[level]:
            if pattern.search(t):
                return level, family
    return "none", ""


def best_region(countries: list[str]) -> str:
    if not countries:
        return "Unknown"
    order = ["France", "Europe (priority)", "Europe (other)", "Rest of world"]
    return min((geo.region_of(c) for c in countries), key=order.index)


def score(title: str, location: str, countries: list[str], description: str = "") -> Score:
    level, family = role_match(title)
    role_pts = ROLE_POINTS.get(level, 0)

    region = best_region(countries)
    geo_pts = GEO_POINTS.get(region, 0)
    loc = _norm(location)
    city_pts = max((pts for city, pts in CITY_BONUS.items() if re.search(rf"\b{city}\b", loc)), default=0)

    text = _norm(f"{title} {description[:500]}")
    timing_pts = sum(pts for pattern, pts in _TIMING if pattern.search(text))

    # No capital-markets signal at all: the offer is not relevant, whatever its location.
    total = 0 if role_pts == 0 else role_pts + geo_pts + city_pts + timing_pts
    return Score(
        total=min(total, 100),
        role_level=level,
        family=family or "Other",
        region=region,
        breakdown={"role": role_pts, "geo": geo_pts, "city": city_pts, "timing": timing_pts},
    )
