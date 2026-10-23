"""Themes and importance score of a news article (French and English keywords)."""

from __future__ import annotations

import re
import unicodedata

# theme key: (weight, keywords). Weights reflect what matters for pricing /
# structuring interviews: derivatives, structured products, volatility and
# central banks first.
THEMES = {
    "central_banks": (40, [
        "bce", "ecb", "fed", "federal reserve", "fomc", "banque centrale", "banques centrales", "central bank",
        "central banks", "taux directeur", "taux directeurs", "policy rate", "rate cut", "rate cuts", "rate hike",
        "rate hikes", "baisse des taux", "hausse des taux", "lagarde", "powell", "bank of england", "boe",
        "bank of japan", "boj", "bns", "snb", "estr", "sofr", "euribor", "monetary policy", "politique monetaire",
        "quantitative tightening", "quantitative easing", "forward guidance", "interest rate", "interest rates",
        "taux d interet",
    ]),
    "vol_derivatives": (40, [
        "volatilite", "volatility", "vix", "vstoxx", "derive", "derives", "derivative", "derivatives", "option",
        "options", "futures", "swaption", "swaptions", "swap", "swaps", "couverture", "hedging",
        "gamma", "skew", "implied vol", "volatilite implicite", "dispersion", "variance",
    ]),
    "structured": (40, [
        "produits structures", "produit structure", "structured product", "structured products", "structured note",
        "structured notes", "autocall", "autocallable", "autocallables", "certificat", "certificats", "warrant",
        "warrants", "capital garanti", "capital protege", "turbo", "turbos", "leonteq", "structuration",
        "structuring",
    ]),
    "credit_sovereign": (25, [
        "credit", "obligation", "obligations", "obligataire", "bond", "bonds", "dette", "dette souveraine",
        "sovereign", "spread", "spreads", "oat", "bund", "bunds", "treasury", "treasuries", "rendement",
        "rendements", "yield", "yields", "notation", "rating", "downgrade", "upgrade", "high yield", "default",
        "defaut", "emission obligataire", "debt",
    ]),
    "fx_commodities": (20, [
        "change", "dollar", "eur usd", "euro dollar", "yen", "yuan", "livre sterling", "sterling", "devise",
        "devises", "currency", "currencies", "forex", "petrole", "brent", "wti", "oil", "crude", "gaz", "gas",
        "gold", "metaux", "metals", "copper", "cuivre", "matieres premieres", "commodity", "commodities", "opep",
        "opec",
    ]),
    "macro_inflation": (20, [
        "inflation", "deflation", "ipc", "cpi", "pce", "pib", "gdp", "croissance", "growth", "chomage",
        "unemployment", "emploi", "payrolls", "jobs report", "recession", "pmi", "deficit", "budget",
        "consommation", "consumer spending", "tarifs douaniers", "tariff", "tariffs", "salaires", "wages",
    ]),
    "regulation": (20, [
        "bale", "basel", "frtb", "amf", "esma", "eba", "acpr", "regulation", "reglementation", "regulator",
        "regulatory", "reglementaire",
        "regulateur", "supervision", "superviseur", "mifid", "emir", "sfdr", "crr", "crd", "stress test",
        "stress tests", "sanction", "sanctions", "sec", "cftc", "prudentiel", "prudential", "capital requirements",
    ]),
    "equities": (15, [
        # "actions" alone is avoided: in English it also means legal or policy actions.
        "marche actions", "marches actions", "les actions", "actions europeennes", "actions americaines",
        "equity", "equities", "stock", "stocks", "bourse", "bourses", "cac 40", "cac",
        "euro stoxx", "stoxx", "s p 500", "nasdaq", "dow jones", "dax", "ftse", "nikkei", "ipo",
        "introduction en bourse", "earnings", "dividende", "dividend", "wall street", "rachat d actions", "buyback",
    ]),
    "banks": (15, [
        "banque", "banques", "bank", "banks", "banking", "bnp", "bnp paribas", "societe generale", "natixis",
        "credit agricole", "jpmorgan", "goldman sachs", "morgan stanley", "citigroup", "ubs", "deutsche bank",
        "hsbc", "barclays", "assureur", "assureurs", "insurer", "insurers", "asset manager", "gestion d actifs",
        "hedge fund", "hedge funds", "private equity", "fintech",
    ]),
}

THEME_LABELS = {
    "central_banks": "Banques centrales et taux",
    "vol_derivatives": "Volatilité et dérivés",
    "structured": "Produits structurés",
    "credit_sovereign": "Crédit et dette souveraine",
    "fx_commodities": "Change et matières premières",
    "macro_inflation": "Macro et inflation",
    "regulation": "Régulation",
    "equities": "Marchés actions",
    "banks": "Banques et secteur financier",
}

OFFICIAL_BONUS = 10          # central banks, BIS, IMF, regulators
MULTI_SOURCE_BONUS = 15      # per additional source covering the story
MULTI_SOURCE_CAP = 30

_PATTERNS = {
    theme: re.compile(r"\b(" + "|".join(re.escape(k) for k in sorted(words, key=len, reverse=True)) + r")\b")
    for theme, (_, words) in THEMES.items()
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def themes_of(title: str, summary: str = "") -> list[str]:
    """Themes found in the article, strongest first. The title counts double."""
    t, s = f" {normalize(title)} ", f" {normalize(summary)} "
    hits = {}
    for theme, pattern in _PATTERNS.items():
        n = 2 * len(pattern.findall(t)) + len(pattern.findall(s))
        if n:
            hits[theme] = n
    return sorted(hits, key=lambda th: (-THEMES[th][0] * hits[th], th))


def score(themes: list[str], n_sources: int = 1, official: bool = False) -> int:
    """Importance 0-100: main theme weight, half of the second, bonuses."""
    weights = sorted((THEMES[t][0] for t in themes), reverse=True)
    points = (weights[0] if weights else 5) + (weights[1] // 2 if len(weights) > 1 else 0)
    points += OFFICIAL_BONUS if official else 0
    points += min(MULTI_SOURCE_CAP, MULTI_SOURCE_BONUS * max(0, n_sources - 1))
    return min(points, 100)
