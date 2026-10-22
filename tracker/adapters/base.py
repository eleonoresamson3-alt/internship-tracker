"""Common helpers for adapters."""

from __future__ import annotations

from datetime import datetime, timezone

from .. import config, filters
from ..http import PoliteClient
from ..models import RawJob, Target


class AdapterError(Exception):
    """Raised by an adapter when an employer cannot be scraped."""


def require(target: Target, *keys: str) -> list:
    missing = [k for k in keys if not target.params.get(k)]
    if missing:
        raise AdapterError(f"missing params in targets.yaml: {', '.join(missing)}")
    return [target.params[k] for k in keys]


def search_terms(target: Target) -> list[str]:
    return target.params.get("search_terms") or config.SEARCH_TERMS


def title_may_match(title: str, employment_type: str = "") -> bool:
    """Cheap pre-filter used before fetching per-offer details."""
    return filters.keep(title, employment_type)


def iso_date(value) -> str:
    """Best-effort conversion of platform dates (ISO strings, epoch ms) to YYYY-MM-DD."""
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)):
        seconds = value / 1000 if value > 10**11 else value
        return datetime.fromtimestamp(seconds, tz=timezone.utc).date().isoformat()
    text = str(value)
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    return ""


def dedupe_raw(jobs: list[RawJob]) -> list[RawJob]:
    seen, out = set(), []
    for job in jobs:
        key = job.native_id or job.url
        if key in seen:
            continue
        seen.add(key)
        out.append(job)
    return out


__all__ = ["AdapterError", "PoliteClient", "RawJob", "Target", "require", "search_terms",
           "title_may_match", "iso_date", "dedupe_raw"]
