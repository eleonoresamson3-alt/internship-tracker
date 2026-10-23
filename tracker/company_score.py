"""Static priority of an employer for the "Entreprises" tab of the site.

Employer type, structuring/pricing specialists and location. The site adds
the time-dependent part: open application window, current offers and the
user's own contact status.
"""

from __future__ import annotations

TYPE_POINTS = {
    "french_bank": 35, "intl_bank": 35, "broker": 35,
    "european_bank": 25, "hedge_fund": 25,
    "asset_manager": 20, "commodities": 20, "software": 20,
    "consulting": 18, "infrastructure": 15, "insurance": 15, "institution": 15,
    "corporate": 12,
}

# Houses known for structured products, derivatives pricing or market-risk work.
SPECIALISTS = {
    "Leonteq", "Kepler Cheuvreux", "Marex", "Exane (BNP Paribas)", "Natixis CIB", "Société Générale",
    "BNP Paribas", "Groupe Crédit Agricole", "CIC Market Solutions", "Vontobel", "EFG International",
    "Banque Cantonale Vaudoise", "Zürcher Kantonalbank", "Julius Baer", "Raiffeisen Bank International",
    "Investec", "Equita", "Commerzbank", "Barclays", "Citi", "JPMorgan", "Goldman Sachs", "Morgan Stanley",
    "Bank of America", "Deutsche Bank", "UBS", "HSBC", "Nomura", "BBVA", "Santander CIB", "ING",
    "Murex", "Numerix", "Orchestrade", "Quantifi", "OpenGamma", "Finalyse", "d-fine",
    "Chappuis Halder & Co", "Quanteam", "Lucht Probst Associates", "Fintegral", "Zanders",
    "Avantage Reply", "Ailancy",
}

# Employers based in France (or recruiting mainly in Paris for these roles).
FRENCH = {
    "Kepler Cheuvreux", "Oddo BHF", "Exane (BNP Paribas)", "Amundi", "AXA IM", "BNP Paribas AM", "Natixis IM",
    "Ostrum", "Mirova", "Carmignac", "Tikehau Capital", "Rothschild & Co", "Edmond de Rothschild", "CFM",
    "Murex", "Orchestrade", "Opensee", "Kaiko", "Flowdesk", "AXA", "CNP Assurances", "SCOR", "Covéa",
    "BNP Paribas Cardif", "Banque de France", "ACPR", "AMF", "Bpifrance", "Caisse des Dépôts",
    "Agence France Trésor", "Ofi Invest", "La Française", "Groupama AM", "Swiss Life AM", "Comgest",
    "DNCA Finance", "Sycomore AM", "TOBAM", "Syquant Capital", "Ossiam", "H2O AM", "Sienna IM", "Moneta AM",
    "Varenne Capital", "Lazard Frères Gestion", "La Financière de l'Echiquier", "Fourpoints IM", "Seeyond",
    "Aequam Capital", "Crédit Mutuel Arkéa", "BRED", "CACEIS", "Chappuis Halder & Co", "Accuracy",
    "Quanteam", "Ailancy", "Square Management", "Exton Consulting", "Sia Partners", "Wavestone",
    "Forvis Mazars", "KPMG", "Grant Thornton", "Capgemini Invent", "Euronext", "TotalEnergies Trading",
    "Engie GEMS", "Danone", "L'Oréal", "LVMH", "Kering", "Hermès", "Pernod Ricard", "Airbus", "Safran",
    "Thales", "Dassault Systèmes", "Renault Group", "Michelin", "Sanofi", "Schneider Electric",
    "Saint-Gobain", "Air Liquide", "Orange", "Vinci", "Bouygues", "Veolia", "EDF", "Carrefour", "Capgemini",
    "Alstom", "Mobilize Financial Services (RCI Bank)", "Air France-KLM",
}
EUROPEAN_TYPES = {"european_bank"}

SPECIALIST_POINTS = 15
FRANCE_POINTS = 15
FRANCE_POINTS_CORPORATE = 5   # treasury desks of large groups stay a secondary option
EUROPE_POINTS = 8


def score(name: str, employer_type: str) -> tuple[int, list[str]]:
    """Return (points, reasons) for the parts that do not change from day to day."""
    points = TYPE_POINTS.get(employer_type, 10)
    reasons = []
    if name in SPECIALISTS:
        points += SPECIALIST_POINTS
        reasons.append("Structuring / pricing reconnu")
    if name in FRENCH or employer_type == "french_bank":
        points += FRANCE_POINTS_CORPORATE if employer_type == "corporate" else FRANCE_POINTS
        reasons.append("France")
    elif employer_type in EUROPEAN_TYPES:
        points += EUROPE_POINTS
        reasons.append("Europe")
    return points, reasons
