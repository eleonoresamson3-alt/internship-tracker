"""Daily market data from free official sources, with 1-day / 1-week / 1-month changes.

Every series is declared in news_sources.yaml (section "market") with its
provider. A series with no legal free source is declared with provider
"unavailable" and shown as "indisponible" on the site: nothing is invented.

Providers:
  ecb         ECB Data Portal API (data-api.ecb.europa.eu), CSV
  bundesbank  Deutsche Bundesbank time-series API, CSV
  fred        Federal Reserve Bank of St. Louis (FRED) public CSV download
  worldbank   World Bank "Pink Sheet" monthly commodity prices (CC BY 4.0), monthly averages
  webstat     Banque de France Webstat API (French government yields); needs a free
              API key in the WEBSTAT_API_KEY environment variable (GitHub secret)
"""

from __future__ import annotations

import csv
import io
import os
import re
from datetime import date, timedelta

from ..http import PoliteClient

HISTORY_DAYS = 60


def _ecb(http: PoliteClient, key: str, days: int = HISTORY_DAYS) -> list[tuple[date, float]]:
    flow, series = key.split("/", 1)
    start = (date.today() - timedelta(days=days)).isoformat()
    text = http.get(f"https://data-api.ecb.europa.eu/service/data/{flow}/{series}?format=csvdata&startPeriod={start}",
                    headers={"Accept": "text/csv"}).text
    rows = csv.DictReader(io.StringIO(text))
    return [(date.fromisoformat(r["TIME_PERIOD"][:10]), float(r["OBS_VALUE"])) for r in rows if r.get("OBS_VALUE")]


def _bundesbank(http: PoliteClient, key: str, days: int = HISTORY_DAYS) -> list[tuple[date, float]]:
    flow, series = key.split("/", 1)
    text = http.get(f"https://api.statistiken.bundesbank.de/rest/download/{flow}/{series}?format=csv&lang=en").text
    points = []
    for row in csv.reader(io.StringIO(text)):
        # Data rows look like "2026-10-22,2.31,"; header and metadata rows are skipped.
        if len(row) >= 2 and len(row[0]) == 10 and row[0][4] == "-":
            try:
                points.append((date.fromisoformat(row[0]), float(row[1])))
            except ValueError:
                continue
    return points[-HISTORY_DAYS:]


def _fred(http: PoliteClient, key: str, days: int = HISTORY_DAYS) -> list[tuple[date, float]]:
    start = (date.today() - timedelta(days=days)).isoformat()
    text = http.get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={key}&cosd={start}").text
    points = []
    for row in csv.reader(io.StringIO(text)):
        if len(row) >= 2 and len(row[0]) == 10 and row[0][4] == "-" and row[1] not in ("", "."):
            points.append((date.fromisoformat(row[0]), float(row[1])))
    return points


class NotConfigured(Exception):
    """The source needs a key that is not set: shown as unavailable, not as an error."""


WEBSTAT_URL = "https://webstat.banque-france.fr/api/explore/v2.1/catalog/datasets"
_DATE_FIELDS = ("time_period_start", "time_period", "date")
_VALUE_FIELDS = ("obs_value", "value")


def parse_webstat(rows: list[dict]) -> list[tuple[date, float]]:
    points = []
    for row in rows:
        day = next((str(row[f])[:10] for f in _DATE_FIELDS if row.get(f)), "")
        value = next((row[f] for f in _VALUE_FIELDS if row.get(f) not in (None, "")), None)
        try:
            points.append((date.fromisoformat(day), float(value)))
        except (TypeError, ValueError):
            continue
    if rows and not points:
        raise ValueError(f"unexpected Webstat fields: {sorted(rows[0])[:15]}")
    return sorted(points)


def _webstat(http: PoliteClient, key: str, days: int = HISTORY_DAYS) -> list[tuple[date, float]]:
    api_key = os.environ.get("WEBSTAT_API_KEY", "").strip()
    if not api_key:
        raise NotConfigured("clé API Webstat (gratuite) non configurée : secret WEBSTAT_API_KEY")
    headers = {"Authorization": f"Apikey {api_key}"}
    # The 100 latest observations (weekends included, as empty values) cover more than a month.
    resp = http.get(f"{WEBSTAT_URL}/observations/records", headers=headers, retries=1, params={
        "where": f'series_key="{key}"', "order_by": "time_period_start desc", "limit": 100,
        "select": "time_period_start,obs_value"}).json()
    rows = resp.get("results", [])
    if not rows:
        # Help fixing the series key: titles of series that look alike.
        stem = key.split(".")[-2] if key.count(".") >= 2 else key
        try:
            alike = http.get(f"{WEBSTAT_URL}/series/records", headers=headers, retries=0,
                             params={"where": f'search("{stem}")', "limit": 10, "select": "series_key"}).json()
            hint = f"; similar keys: {[r.get('series_key') for r in alike.get('results', [])]}"
        except Exception:
            hint = ""
        raise ValueError(f"no observation for {key}{hint}")
    cutoff = date.today() - timedelta(days=days)
    return [p for p in parse_webstat(rows) if p[0] >= cutoff]


WORLDBANK_PAGE = "https://www.worldbank.org/en/research/commodity-markets"


def parse_pink_sheet(rows: list[tuple], column: str) -> list[tuple[date, float]]:
    """Monthly values of one commodity from the 'Monthly Prices' sheet rows."""
    header = next((r for r in rows[:15] if any(isinstance(c, str) and c.strip() == column for c in r)), None)
    if header is None:
        raise ValueError(f"column {column!r} not found in the Pink Sheet")
    col = next(i for i, c in enumerate(header) if isinstance(c, str) and c.strip() == column)
    points = []
    for r in rows:
        m = re.fullmatch(r"(\d{4})M(\d{2})", str(r[0] or ""))
        if m and col < len(r) and isinstance(r[col], (int, float)):
            points.append((date(int(m[1]), int(m[2]), 1), float(r[col])))
    return points


def _worldbank(http: PoliteClient, key: str, days: int = HISTORY_DAYS) -> list[tuple[date, float]]:
    import openpyxl  # only needed for this provider

    page = http.get(WORLDBANK_PAGE).text
    links = re.findall(r'https://thedocs\.worldbank\.org/[^"\']+CMO-Historical-Data-Monthly\.xlsx', page)
    if not links:
        raise ValueError("Pink Sheet link not found on the World Bank page")
    book = openpyxl.load_workbook(io.BytesIO(http.get(links[0]).content), read_only=True, data_only=True)
    rows = list(book["Monthly Prices"].iter_rows(values_only=True))
    return parse_pink_sheet(rows, key)[-24:]


PROVIDERS = {"ecb": _ecb, "bundesbank": _bundesbank, "fred": _fred, "webstat": _webstat, "worldbank": _worldbank}


def _value_on_or_before(points: list[tuple[date, float]], day: date):
    candidates = [v for d, v in points if d <= day]
    return candidates[-1] if candidates else None


STEP_HISTORY_DAYS = 800   # policy rates only change at meetings: look further back


def changes(points: list[tuple[date, float]], unit: str, step: bool = False, today: date | None = None) -> dict:
    """Last value and changes: in % for prices and indices, in basis points for rates.

    step: the series only has a point when the value changes (policy rates); the
    value holds until the next point, so changes are measured from today."""
    points = sorted(points)
    last_day, last = points[-1]
    if step:
        today = today or date.today()
        previous = _value_on_or_before(points, today - timedelta(days=1))
        week = _value_on_or_before(points, today - timedelta(days=7))
        month = _value_on_or_before(points, today - timedelta(days=30))
        last_day = today
    else:
        previous = points[-2][1] if len(points) > 1 else None
        week = _value_on_or_before(points, last_day - timedelta(days=7))
        month = _value_on_or_before(points, last_day - timedelta(days=30))

    def delta(ref):
        if ref is None or ref == 0:
            return None
        if unit == "%":   # rates: change in basis points
            return round((last - ref) * 100, 1)
        return round((last / ref - 1) * 100, 2)

    return {"value": last, "date": last_day.isoformat(), "d1": delta(previous), "w1": delta(week), "m1": delta(month)}


def monthly_changes(points: list[tuple[date, float]], unit: str) -> dict:
    """Monthly averages: last month's level and its change over 1 month (no daily or weekly change)."""
    points = sorted(points)
    (last_day, last), previous = points[-1], (points[-2][1] if len(points) > 1 else None)
    month = changes(points[-2:], unit)["d1"] if previous is not None else None
    return {"value": last, "date": last_day.isoformat(), "period": last_day.isoformat()[:7],
            "d1": None, "w1": None, "m1": month}


def fetch_all(series: list[dict], http: PoliteClient) -> tuple[list[dict], list[dict]]:
    out, errors = [], []
    for s in series:
        row = {k: s.get(k, "") for k in ("key", "label", "group", "unit", "provider", "note")}
        provider = PROVIDERS.get(s.get("provider", ""))
        if provider is None:
            row["status"] = "indisponible"
            out.append(row)
            continue
        try:
            step = bool(s.get("step"))
            points = provider(http, s["series"], STEP_HISTORY_DAYS) if step else provider(http, s["series"])
            if not points:
                raise ValueError("no data returned")
            if s.get("monthly"):
                row.update(monthly_changes(points, s.get("unit", "")))
            else:
                row.update(changes(points, s.get("unit", ""), step))
            row["status"] = "ok"
        except NotConfigured as exc:
            row["status"] = "indisponible"
            row["note"] = str(exc)
        except Exception as exc:  # one series failing never stops the others
            row["status"] = "indisponible"
            errors.append({"source": f"marché: {s['label']}", "error": f"{type(exc).__name__}: {exc}"[:300]})
        out.append(row)
    return out, errors
