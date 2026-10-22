"""History of offers: merge a run into data/jobs.json and derive the daily files."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from . import config
from .models import normalize_title


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=False) + "\n", encoding="utf-8")


def dedupe_key(job: dict) -> str:
    """Two offers from the same employer with the same title and location are one offer."""
    return "|".join([job["employer"], normalize_title(job["title"]), normalize_title(job.get("location", ""))])


def dedupe(jobs: list[dict]) -> list[dict]:
    by_key: dict[str, dict] = {}
    for job in jobs:
        key = dedupe_key(job)
        kept = by_key.get(key)
        if kept is None or job["score"] > kept["score"]:
            by_key[key] = job
    return list(by_key.values())


def merge(history: list[dict], scraped: list[dict], run_date: str,
          failed_employers: set[str], prune_after_days: int = config.PRUNE_AFTER_DAYS) -> list[dict]:
    """Merge today's offers into the history.

    - new offers get first_seen = run_date;
    - offers seen again keep their first_seen and get last_seen = run_date;
    - offers not seen today are marked inactive, unless their employer failed
      today (a scraping error must not look like a closed offer);
    - inactive offers not seen for `prune_after_days` are dropped.
    """
    by_id = {job["id"]: job for job in history}
    # Map old offers by dedupe key too, so an id change on the platform side
    # (re-posting) does not make an old offer look new.
    by_key = {dedupe_key(job): job for job in history}

    seen_ids = set()
    for job in scraped:
        old = by_id.get(job["id"]) or by_key.get(dedupe_key(job))
        if old:
            job["first_seen"] = old["first_seen"]
            if old["id"] != job["id"]:
                by_id.pop(old["id"], None)
        else:
            job["first_seen"] = run_date
        job["last_seen"] = run_date
        job["active"] = True
        by_id[job["id"]] = job
        seen_ids.add(job["id"])

    cutoff = (date.fromisoformat(run_date) - timedelta(days=prune_after_days)).isoformat()
    merged = []
    for job_id, job in by_id.items():
        if job_id not in seen_ids and job["employer"] not in failed_employers:
            job["active"] = False
        if not job["active"] and job["last_seen"] < cutoff:
            continue
        merged.append(job)
    merged.sort(key=lambda j: (not j["active"], -j["score"], j["employer"], j["title"]))
    return merged


def new_today(jobs: list[dict], run_date: str) -> list[dict]:
    return sorted((j for j in jobs if j["active"] and j["first_seen"] == run_date),
                  key=lambda j: -j["score"])
