"""Daily market data from free official sources, with 1-day / 1-week / 1-month changes.

Every series is declared in news_sources.yaml (section "market") with its
provider. A series with no legal free source is declared with provider
"unavailable" and shown as "indisponible" on the site: nothing is invented.

Providers:
  ecb         ECB Data Portal API (data-api.ecb.europa.eu), CSV
  bundesbank  Deutsche Bundesbank time-series API, CSV
  fred        Federal Reserve Bank of St. Louis (FRED) public CSV download
"""

from __future__ import annotations

import csv
import io
from datetime import date, timedelta

from ..http import PoliteClient

HISTORY_DAYS = 60


def _ecb(http: PoliteClient, key: str) -> list[tuple[date, float]]:
    flow, series = key.split("/", 1)
    start = (date.today() - timedelta(days=HISTORY_DAYS)).isoformat()
    text = http.get(f"https://data-api.ecb.europa.eu/service/data/{flow}/{series}?format=csvdata&startPeriod={start}",
                    headers={"Accept": "text/csv"}).text
    rows = csv.DictReader(io.StringIO(text))
    return [(date.fromisoformat(r["TIME_PERIOD"][:10]), float(r["OBS_VALUE"])) for r in rows if r.get("OBS_VALUE")]


def _bundesbank(http: PoliteClient, key: str) -> list[tuple[date, float]]:
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


def _fred(http: PoliteClient, key: str) -> list[tuple[date, float]]:
    start = (date.today() - timedelta(days=HISTORY_DAYS)).isoformat()
    text = http.get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={key}&cosd={start}").text
    points = []
    for row in csv.reader(io.StringIO(text)):
        if len(row) >= 2 and len(row[0]) == 10 and row[0][4] == "-" and row[1] not in ("", "."):
            points.append((date.fromisoformat(row[0]), float(row[1])))
    return points


PROVIDERS = {"ecb": _ecb, "bundesbank": _bundesbank, "fred": _fred}


def _value_on_or_before(points: list[tuple[date, float]], day: date):
    candidates = [v for d, v in points if d <= day]
    return candidates[-1] if candidates else None


def changes(points: list[tuple[date, float]], unit: str) -> dict:
    """Last value and changes: in % for prices and indices, in basis points for rates."""
    points = sorted(points)
    last_day, last = points[-1]
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
            points = provider(http, s["series"])
            if not points:
                raise ValueError("no data returned")
            row.update(changes(points, s.get("unit", "")))
            row["status"] = "ok"
        except Exception as exc:  # one series failing never stops the others
            row["status"] = "indisponible"
            errors.append({"source": f"marché: {s['label']}", "error": f"{type(exc).__name__}: {exc}"[:300]})
        out.append(row)
    return out, errors
