"""Daily news watch: fetch feeds and market data, classify, dedupe, store.

    python -m tracker.news.run
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import yaml

from .. import config, store
from ..http import PoliteClient
from . import calendar, classify, dedupe, feeds, market

log = logging.getLogger("news")
KEEP_DAYS = 30
STALE_DAYS = 14


def load_sources(path=config.NEWS_SOURCES_FILE) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def fetch_feeds(sources: list[dict], http: PoliteClient):
    items, errors, stats = [], [], []

    def one(source):
        try:
            return source, feeds.fetch(source, http), None
        except Exception as exc:  # one feed failing never stops the others
            return source, [], f"{type(exc).__name__}: {exc}"[:300]

    with ThreadPoolExecutor(max_workers=6) as pool:
        for source, got, error in pool.map(one, sources):
            if error:
                errors.append({"source": source["name"], "url": source["url"], "error": error})
                log.warning("%-30s FAILED: %s", source["name"], error)
                continue
            for item in got:
                item["official"] = bool(source.get("official"))
            items.extend(got)
            dates = sorted(i["published"] for i in got if i["published"])
            if dates and dates[-1] < (datetime.now(timezone.utc) - timedelta(days=STALE_DAYS)).isoformat():
                # A feed that still answers but stopped being updated (its items fall out of the history).
                errors.append({"source": source["name"], "url": source["url"],
                               "error": f"stale feed: newest item published {dates[-1][:10]}"})
                log.warning("%-30s STALE: newest item %s", source["name"], dates[-1])
            stats.append({"source": source["name"], "items": len(got),
                          "newest": dates[-1] if dates else "", "oldest": dates[0] if dates else ""})
            log.info("%-30s %3d items", source["name"], len(got))
    return items, errors, stats


def build_records(items: list[dict], now: datetime) -> list[dict]:
    """Classify, group the same story across sources, score."""
    for item in items:
        item["themes"] = classify.themes_of(item["title"], item["summary"])
    records = []
    for group in dedupe.cluster(items):
        # Keep the version with a summary and the earliest publication time.
        lead = sorted(group, key=lambda i: (not i["summary"], i["published"] or "9999"))[0]
        themes = list(dict.fromkeys(t for i in group for t in i["themes"]))
        records.append({
            "id": lead["id"],
            "title": lead["title"],
            "link": lead["link"],
            "source": lead["source"],
            "sources": sorted({i["source"] for i in group}),
            "published": lead["published"],
            "summary": lead["summary"],
            "themes": themes,
            "official": any(i["official"] for i in group),
            "first_seen": now.isoformat(timespec="minutes"),
        })
    return records


def rescore(records: list[dict]) -> None:
    """Re-classify and re-score every record, so keyword changes also apply to the history."""
    for r in records:
        r["themes"] = classify.themes_of(r["title"], r.get("summary", ""))
        r["score"] = classify.score(r["themes"], len(r["sources"]), r.get("official", False))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--all", action="store_true", help="also try feeds marked enabled: false (to test them)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    now = datetime.now(timezone.utc)
    sources = load_sources()
    feed_sources = [f for f in sources.get("feeds", []) if args.all or f.get("enabled", True)]
    http = PoliteClient()

    items, feed_errors, stats = fetch_feeds(feed_sources, http)
    fresh = build_records(items, now)
    rescore(fresh)

    history = store.load_json(config.NEWS_FILE, {}).get("items", [])
    merged = dedupe.merge_history(history, fresh, now, KEEP_DAYS)
    rescore(merged)

    series, market_errors = market.fetch_all(sources.get("market", []), http)
    meetings, calendar_errors = calendar.fetch_all(sources.get("calendar_manual", []), http)
    recent = (now - timedelta(days=30)).date().isoformat()
    meetings = [m for m in meetings if m["end"] >= recent]   # past years are of no use on the site
    generated_at = now.isoformat(timespec="seconds")
    store.save_json(config.NEWS_FILE, {"generated_at": generated_at, "items": merged})
    store.save_json(config.MARKET_FILE, {"generated_at": generated_at, "series": series})
    store.save_json(config.CALENDAR_FILE, {"generated_at": generated_at, "meetings": meetings})
    errors = feed_errors + market_errors + calendar_errors
    store.save_json(config.NEWS_ERRORS_FILE, {"generated_at": generated_at, "errors": errors, "stats": stats})

    ok = sum(1 for s in series if s["status"] == "ok")
    summary = (f"{len(fresh)} articles fetched, {len(merged)} in 30-day history, "
               f"{len(feed_errors)}/{len(feed_sources)} feeds failed, {ok}/{len(series)} market series available, "
               f"{len(meetings)} central bank meetings")
    log.info(summary)
    if os.environ.get("GITHUB_ACTIONS"):
        kept = {}
        for r in merged:
            for src in r["sources"]:
                kept[src] = kept.get(src, 0) + 1
        lines = [summary] + [f"{s['source']}: {s['items']} fetched, {kept.get(s['source'], 0)} in history "
                             f"(published {s['oldest'] or '?'} → {s['newest'] or '?'})" for s in stats] + \
                [f"FAILED {e['source']}: {e['error'][:200]}" for e in errors]
        print("::notice title=News summary::" + "%0A".join(l.replace("%", "%25") for l in lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
