"""Country detection from free-text locations, and geographic priority."""

from __future__ import annotations

import re
import unicodedata

FRANCE = "FR"
# Priority Europe, in the order given by the user.
EUROPE_PRIORITY = ["LU", "CH", "BE", "GB", "DE", "NL", "IT", "ES"]
EUROPE_OTHER = [
    "IE", "PT", "AT", "PL", "CZ", "SE", "DK", "NO", "FI", "GR", "HU", "RO",
    "MC", "MT", "CY", "SK", "SI", "HR", "BG", "EE", "LV", "LT", "IS", "LI", "RS",
]

COUNTRY_NAMES = {
    "FR": "France", "LU": "Luxembourg", "CH": "Switzerland", "BE": "Belgium",
    "GB": "United Kingdom", "DE": "Germany", "NL": "Netherlands", "IT": "Italy",
    "ES": "Spain", "IE": "Ireland", "PT": "Portugal", "AT": "Austria",
    "PL": "Poland", "CZ": "Czech Republic", "SE": "Sweden", "DK": "Denmark",
    "NO": "Norway", "FI": "Finland", "GR": "Greece", "HU": "Hungary",
    "RO": "Romania", "MC": "Monaco", "MT": "Malta", "CY": "Cyprus",
    "SK": "Slovakia", "SI": "Slovenia", "HR": "Croatia", "BG": "Bulgaria",
    "EE": "Estonia", "LV": "Latvia", "LT": "Lithuania", "IS": "Iceland",
    "LI": "Liechtenstein", "RS": "Serbia",
    "US": "United States", "CA": "Canada", "MX": "Mexico", "BR": "Brazil",
    "AR": "Argentina", "CL": "Chile", "CO": "Colombia",
    "HK": "Hong Kong", "SG": "Singapore", "JP": "Japan", "CN": "China",
    "KR": "South Korea", "TW": "Taiwan", "IN": "India", "AU": "Australia",
    "NZ": "New Zealand", "AE": "United Arab Emirates", "QA": "Qatar",
    "SA": "Saudi Arabia", "BH": "Bahrain", "IL": "Israel", "ZA": "South Africa",
    "MA": "Morocco", "TR": "Turkey", "MY": "Malaysia", "TH": "Thailand",
    "PH": "Philippines", "ID": "Indonesia", "VN": "Vietnam",
}

_EXTRA_COUNTRY_ALIASES = {
    "FR": ["francia", "frankreich"],
    "LU": ["luxemburg", "lussemburgo", "grand duchy of luxembourg"],
    "CH": ["suisse", "schweiz", "svizzera", "switzerland"],
    "BE": ["belgique", "belgie", "belgien", "belgium"],
    "GB": ["uk", "u k", "england", "scotland", "wales", "great britain", "royaume uni", "britain"],
    "DE": ["allemagne", "deutschland"],
    "NL": ["pays bas", "nederland", "the netherlands", "holland"],
    "IT": ["italie", "italia"],
    "ES": ["espagne", "espana"],
    "IE": ["irlande"],
    "PT": ["portugal"],
    "AT": ["autriche", "osterreich"],
    "PL": ["pologne", "polska"],
    "CZ": ["czechia", "republique tcheque"],
    "US": ["usa", "u s a", "united states of america", "etats unis", "us"],
    "AE": ["uae", "emirats arabes unis"],
    "HK": ["hong kong sar", "hksar"],
    "JP": ["japon"],
    "CN": ["chine", "mainland china"],
    "SG": ["singapour"],
    "IN": ["inde"],
}

CITIES = {
    "FR": ["paris", "la defense", "puteaux", "courbevoie", "montrouge", "nanterre",
           "saint denis", "neuilly sur seine", "boulogne billancourt", "issy les moulineaux",
           "levallois perret", "lyon", "marseille", "lille", "nantes", "bordeaux",
           "toulouse", "nice", "strasbourg", "guyancourt", "ile de france"],
    "LU": ["luxembourg city", "kirchberg", "strassen", "bertrange", "leudelange"],
    "CH": ["zurich", "geneva", "geneve", "genf", "lausanne", "lugano", "basel", "bale",
           "bern", "berne", "zug", "neuchatel", "nyon"],
    "BE": ["brussels", "bruxelles", "brussel", "antwerp", "anvers", "antwerpen",
           "ghent", "gent", "liege", "leuven"],
    "GB": ["london", "londres", "edinburgh", "glasgow", "birmingham", "manchester",
           "leeds", "bristol", "canary wharf", "knutsford", "northampton", "belfast",
           "bournemouth", "cambridge", "oxford"],
    "DE": ["frankfurt", "francfort", "munich", "munchen", "berlin", "dusseldorf",
           "hamburg", "stuttgart", "cologne", "koln", "eschborn", "hanover", "hannover",
           "mainz", "wiesbaden"],
    "NL": ["amsterdam", "rotterdam", "utrecht", "the hague", "den haag", "eindhoven"],
    "IT": ["milan", "milano", "rome", "roma", "turin", "torino", "bologna", "florence",
           "firenze", "verona", "trieste"],
    "ES": ["madrid", "barcelona", "bilbao", "valencia", "seville", "sevilla", "boadilla"],
    "IE": ["dublin", "cork", "limerick"],
    "PT": ["lisbon", "lisboa", "porto"],
    "AT": ["vienna", "wien"],
    "PL": ["warsaw", "warszawa", "krakow", "wroclaw", "lodz"],
    "CZ": ["prague", "praha"],
    "SE": ["stockholm"], "DK": ["copenhagen"], "NO": ["oslo"], "FI": ["helsinki"],
    "GR": ["athens"], "HU": ["budapest"], "RO": ["bucharest"], "MC": ["monte carlo"],
    "US": ["new york", "nyc", "chicago", "boston", "greenwich", "stamford",
           "san francisco", "los angeles", "miami", "austin", "houston", "dallas",
           "charlotte", "jersey city", "philadelphia", "seattle", "atlanta",
           "washington dc", "washington d c", "bala cynwyd", "princeton", "palo alto",
           "menlo park", "salt lake city", "wilmington", "pittsburgh", "columbus",
           "tampa", "denver", "minneapolis"],
    "CA": ["toronto", "montreal", "vancouver", "calgary", "ottawa"],
    "MX": ["mexico city"], "BR": ["sao paulo", "rio de janeiro"],
    "HK": ["hong kong", "kowloon"],
    "SG": ["singapore"],
    "JP": ["tokyo", "osaka"],
    "CN": ["shanghai", "beijing", "shenzhen", "guangzhou"],
    "KR": ["seoul"], "TW": ["taipei"],
    "IN": ["mumbai", "bangalore", "bengaluru", "pune", "chennai", "hyderabad",
           "gurgaon", "gurugram", "new delhi", "noida", "kolkata"],
    "AU": ["sydney", "melbourne", "brisbane", "perth"],
    "AE": ["dubai", "abu dhabi"], "QA": ["doha"], "SA": ["riyadh"], "BH": ["manama"],
    "IL": ["tel aviv"], "ZA": ["johannesburg", "cape town"], "MA": ["casablanca"],
    "TR": ["istanbul"], "MY": ["kuala lumpur"],
}

US_STATES = {
    "ny", "nj", "ct", "ma", "il", "ca", "tx", "fl", "nc", "pa", "wa", "ga", "dc",
    "de", "oh", "co", "ut", "mn", "va", "md", "az", "or", "mi", "tn",
}

# Some ISO codes collide with US state codes or common words, so they are only
# accepted as a whole location segment (e.g. "Paris, FR").
_AMBIGUOUS_CODES = {"DE", "CA", "IN", "IL", "PA", "MA", "CO", "AR", "ID", "SA", "NO", "IT", "MT"}


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _build_patterns():
    patterns: list[tuple[re.Pattern, str]] = []
    for code, name in COUNTRY_NAMES.items():
        for alias in [name] + _EXTRA_COUNTRY_ALIASES.get(code, []):
            patterns.append((re.compile(rf"\b{re.escape(_norm(alias))}\b"), code))
    for code, cities in CITIES.items():
        for city in cities:
            patterns.append((re.compile(rf"\b{re.escape(_norm(city))}\b"), code))
    # Longer aliases first, so "new york" wins over "york" and similar overlaps.
    patterns.sort(key=lambda p: -len(p[0].pattern))
    return patterns


_PATTERNS = _build_patterns()


def detect_countries(location: str) -> list[str]:
    """Return the ISO country codes mentioned in a free-text location."""
    if not location:
        return []
    found: list[str] = []
    norm = _norm(location)
    for pattern, code in _PATTERNS:
        if pattern.search(norm) and code not in found:
            found.append(code)
    # "Luxembourg" alone is both a city and a country: already mapped to LU.
    # Two-letter segments: "Paris, FR", "London, UK", "Chicago, IL".
    for segment in re.split(r"[,;/|()\-–]", location):
        code = segment.strip()
        if not (len(code) == 2 and code.isalpha() and code.isupper()):
            continue
        if code == "UK":
            code = "GB"
        is_state = code.lower() in US_STATES
        if is_state and (code not in COUNTRY_NAMES or (code in _AMBIGUOUS_CODES and not found)):
            code = "US"
        elif code in _AMBIGUOUS_CODES and found:
            continue  # e.g. "Frankfurt, DE" already resolved through the city
        if code in COUNTRY_NAMES and code not in found:
            found.append(code)
    return found


def country_name(code: str) -> str:
    return COUNTRY_NAMES.get(code, code)


def region_of(code: str) -> str:
    if code == FRANCE:
        return "France"
    if code in EUROPE_PRIORITY:
        return "Europe (priority)"
    if code in EUROPE_OTHER:
        return "Europe (other)"
    return "Rest of world"


def normalize_country(value: str) -> str:
    """Map a platform-provided country (ISO code or name) to an ISO code."""
    if not value:
        return ""
    value = value.strip()
    if len(value) == 2 and value.upper() in COUNTRY_NAMES:
        return value.upper()
    if value.upper() == "UK":
        return "GB"
    if len(value) == 3 and value.isupper():
        iso3 = {"FRA": "FR", "GBR": "GB", "USA": "US", "DEU": "DE", "CHE": "CH",
                "LUX": "LU", "BEL": "BE", "NLD": "NL", "ITA": "IT", "ESP": "ES",
                "HKG": "HK", "SGP": "SG", "JPN": "JP", "IRL": "IE", "ARE": "AE",
                "IND": "IN", "CAN": "CA", "AUS": "AU", "CHN": "CN", "POL": "PL"}
        if value in iso3:
            return iso3[value]
    codes = detect_countries(value)
    return codes[0] if codes else ""
