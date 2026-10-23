"""Entry point: scrape every employer in targets.yaml and update data/.

    python -m tracker.run                  # all enabled employers
    python -m tracker.run --only "Jane Street" --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from urllib.parse import urlsplit

import yaml

from . import config, deadlines, filters, geo, scoring, store, timing
from .adapters import get_adapter
from .http import PoliteClient
from .models import RawJob, Target

log = logging.getLogger("tracker")


def load_targets(path=config.TARGETS_FILE) -> list[Target]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [Target(**entry) for entry in raw.get("employers", [])]


def job_id(target: Target, raw: RawJob) -> str:
    native = raw.native_id or raw.url
    digest = hashlib.sha1(native.encode()).hexdigest()[:12]
    return f"{target.slug}-{digest}"


def to_record(target: Target, raw: RawJob) -> dict | None:
    """Filter and score one raw offer. Returns None when the offer is not kept."""
    title = " ".join((raw.title or "").split())
    employment_type = raw.employment_type
    if target.params.get("internship_in_description") and filters.description_says_internship(raw.description):
        employment_type = f"{employment_type} Internship"
    if not title or not raw.url or not filters.keep(title, employment_type):
        return None
    if target.type == "corporate" and not filters.corporate_markets_role(title):
        return None
    countries = list(dict.fromkeys(
        [c for c in raw.countries if c] + geo.detect_countries(raw.location)))
    if not countries:
        # Many HTML job lists give no location: try the title ("... - London"),
        # then the offer URL ("/emploi/courbevoie/..."), then the employer default.
        path = urlsplit(raw.url).path.replace("-", " ").replace("/", " ")
        countries = geo.detect_countries(title) or geo.detect_countries(path)
    if not countries and target.params.get("default_country"):
        countries = [target.params["default_country"]]
    when = timing.analyse(title, raw.description)
    first, last = config.year_window()
    if when.year and not first <= when.year <= last:
        return None  # start year stated in the ad, outside the window
    if when.year and when.month and config.starts_too_early(when.year, when.month):
        return None  # e.g. "Stage - Mars 2027" when the earliest start is June 2027
    deadline = deadlines.parse(raw.description)
    if deadline and deadline < date.today():
        return None  # the ad says applications are closed
    deadline_source = "annonce" if deadline else ""
    if not deadline:
        deadline = deadlines.estimate(target.type, when)
        deadline_source = "estimée" if deadline else ""
    s = scoring.score(title, raw.location, countries, when)
    if s.total < config.MIN_SCORE:
        return None
    return {
        "id": job_id(target, raw),
        "employer": target.name,
        "employer_type": target.type,
        "platform": target.platform,
        "title": title,
        "location": raw.location,
        "countries": countries,
        "country_names": [geo.country_name(c) for c in countries],
        "region": s.region,
        "family": s.family,
        "role_level": s.role_level,
        "score": s.total,
        "score_breakdown": s.breakdown,
        "timing": when.kind,
        "start": when.start,
        "deadline": deadline.isoformat() if deadline else "",
        "deadline_source": deadline_source,
        "url": raw.url,
        "posted_at": raw.posted_at,
    }


def scrape_one(target: Target, http: PoliteClient):
    """Returns (records, error, stat, debug_titles) for one employer; never raises."""
    started = datetime.now(timezone.utc)
    try:
        raw_jobs = get_adapter(target.platform).fetch(target, http)
    except Exception as exc:  # one employer failing must never stop the run
        log.warning("%-35s FAILED: %s", target.name, exc)
        log.debug(traceback.format_exc())
        return [], {
            "employer": target.name,
            "platform": target.platform,
            "careers_url": target.careers_url,
            "error": f"{type(exc).__name__}: {exc}"[:500],
            "at": started.isoformat(timespec="seconds"),
        }, None, []
    kept = [r for r in (to_record(target, raw) for raw in raw_jobs) if r]
    log.info("%-35s %4d offers fetched, %3d kept", target.name, len(raw_jobs), len(kept))
    titles = sorted({f"{r.title} | {r.location}" for r in raw_jobs})
    return kept, None, {"employer": target.name, "fetched": len(raw_jobs), "kept": len(kept)}, titles


def scrape(targets: list[Target], http: PoliteClient, debug: dict | None = None,
           workers: int = config.WORKERS):
    records, errors, stats = [], [], []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda t: scrape_one(t, http), targets))
    for target, (kept, error, stat, titles) in zip(targets, results):
        records.extend(kept)
        if error:
            errors.append(error)
        if stat:
            stats.append(stat)
        if debug is not None:
            debug[target.name] = titles
    return records, errors, stats


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", action="append", help="scrape only this employer (repeatable)")
    parser.add_argument("--dry-run", action="store_true", help="print results, do not write data/")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--debug-titles", action="store_true",
                        help="also write data/debug_titles.json with every fetched title (development aid)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    targets = [t for t in load_targets() if t.enabled]
    if args.only:
        wanted = {name.lower() for name in args.only}
        targets = [t for t in targets if t.name.lower() in wanted]
    now = datetime.now(timezone.utc)
    run_date = now.date().isoformat()

    debug = {} if args.debug_titles else None
    records, errors, stats = scrape(targets, PoliteClient(), debug)
    if debug is not None:
        store.save_json(config.DATA_DIR / "debug_titles.json", debug)
    records = store.dedupe(records)

    if args.dry_run:
        for r in sorted(records, key=lambda r: -r["score"]):
            print(f"{r['score']:3d}  {r['employer']:<25} {r['title'][:70]:<70} {r['location'][:40]}")
        for e in errors:
            print(f"ERROR {e['employer']}: {e['error']}", file=sys.stderr)
        return 0

    history = store.load_json(config.JOBS_FILE, {}).get("jobs", [])
    failed = {e["employer"] for e in errors}
    if args.only:
        # Partial run: employers that were not scraped must not be marked closed.
        failed |= {j["employer"] for j in history} - {t.name for t in targets}
    jobs = store.merge(history, records, run_date, failed)
    fresh = store.new_today(jobs, run_date)
    generated_at = now.isoformat(timespec="seconds")

    store.save_json(config.JOBS_FILE, {"generated_at": generated_at, "jobs": jobs})
    store.save_json(config.NEW_TODAY_FILE, {"generated_at": generated_at, "date": run_date, "jobs": fresh})
    store.save_json(config.ERRORS_FILE, {
        "generated_at": generated_at,
        "employers_total": len(targets),
        "employers_failed": len(errors),
        "errors": errors,
        "stats": stats,
    })
    summary = (f"{sum(j['active'] for j in jobs)} active offers, {len(fresh)} new today, "
               f"{len(errors)}/{len(targets)} employers failed")
    log.info(summary)
    if os.environ.get("GITHUB_ACTIONS"):
        # Annotations are visible on the run page (and through the API) without opening the logs.
        lines = [summary] + [f"{s['employer']}: {s['fetched']} fetched, {s['kept']} kept" for s in stats]
        lines += [f"FAILED {e['employer']}: {e['error'][:200]}" for e in errors]
        print("::notice title=Scrape summary::" + "%0A".join(l.replace("%", "%25") for l in lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
