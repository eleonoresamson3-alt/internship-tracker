"""Morning analyses: format check and housekeeping of data/analyses.json.

    python -m tracker.news.analyses --check    # exit 1 and list the problems if the file is invalid
    python -m tracker.news.analyses --prune    # drop days older than KEEP_DAYS, newest first

The analyses are written each morning by a scheduled Claude Code session that
follows ANALYSES.md; this module only checks what it wrote, so a malformed file
never reaches the site.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, timedelta

from .. import config, store
from ..sanitize import safe_url
from .classify import THEMES

KEEP_DAYS = 30
MAX_ARTICLES = 6
MAX_ARTICLE_WORDS = 900

_DATE = re.compile(r"\d{4}-\d{2}-\d{2}$")


def _text(value, where: str, problems: list[str], required: bool = True) -> None:
    if not isinstance(value, str) or (required and not value.strip()):
        problems.append(f"{where}: text expected")


def validate(data: dict) -> list[str]:
    """Problems found in the analyses file (empty list when it is valid)."""
    problems: list[str] = []
    days = data.get("days") if isinstance(data, dict) else None
    if not isinstance(days, list):
        return ["'days' list missing"]
    seen = set()
    for d, day in enumerate(days):
        where = f"days[{d}]"
        if not isinstance(day, dict):
            problems.append(f"{where}: object expected")
            continue
        if not _DATE.match(str(day.get("date", ""))):
            problems.append(f"{where}.date: YYYY-MM-DD expected")
        elif day["date"] in seen:
            problems.append(f"{where}.date: {day['date']} appears twice")
        seen.add(day.get("date"))
        brief = day.get("brief", [])
        if not isinstance(brief, list) or not all(isinstance(b, str) and b.strip() for b in brief):
            problems.append(f"{where}.brief: list of sentences expected")
        articles = day.get("articles")
        if not isinstance(articles, list) or not 1 <= len(articles) <= MAX_ARTICLES:
            problems.append(f"{where}.articles: 1 to {MAX_ARTICLES} articles expected")
            continue
        for a, art in enumerate(articles):
            w = f"{where}.articles[{a}]"
            if not isinstance(art, dict):
                problems.append(f"{w}: object expected")
                continue
            for key in ("title", "lead", "what", "why", "impact"):
                _text(art.get(key), f"{w}.{key}", problems)
            if art.get("theme") not in THEMES:
                problems.append(f"{w}.theme: one of {', '.join(THEMES)}")
            words = sum(len(str(art.get(k, "")).split()) for k in ("lead", "what", "why", "impact"))
            if words > MAX_ARTICLE_WORDS:
                problems.append(f"{w}: {words} words, at most {MAX_ARTICLE_WORDS}")
            interview = art.get("interview")
            if not isinstance(interview, dict):
                problems.append(f"{w}.interview: object expected")
            else:
                _text(interview.get("question"), f"{w}.interview.question", problems)
                hints = interview.get("hints", [])
                if not isinstance(hints, list) or not all(isinstance(h, str) for h in hints):
                    problems.append(f"{w}.interview.hints: list of strings expected")
            for g, item in enumerate(art.get("glossary", []) or []):
                if not isinstance(item, dict):
                    problems.append(f"{w}.glossary[{g}]: object expected")
                    continue
                _text(item.get("term"), f"{w}.glossary[{g}].term", problems)
                _text(item.get("definition"), f"{w}.glossary[{g}].definition", problems)
            sources = art.get("sources")
            if not isinstance(sources, list) or not sources:
                problems.append(f"{w}.sources: at least one source expected")
                continue
            for s, src in enumerate(sources):
                if not isinstance(src, dict) or not str(src.get("url", "")).startswith("https://") \
                        or not safe_url(src.get("url")):
                    problems.append(f"{w}.sources[{s}]: object with an https url expected")
                else:
                    _text(src.get("title"), f"{w}.sources[{s}].title", problems)
    return problems


def prune(data: dict, today: date | None = None, keep_days: int = KEEP_DAYS) -> dict:
    cutoff = ((today or date.today()) - timedelta(days=keep_days)).isoformat()
    days = [d for d in data.get("days", []) if d.get("date", "") >= cutoff]
    days.sort(key=lambda d: d["date"], reverse=True)
    return {**data, "days": days}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="validate data/analyses.json")
    parser.add_argument("--prune", action="store_true", help=f"keep the last {KEEP_DAYS} days only")
    args = parser.parse_args(argv)
    data = store.load_json(config.ANALYSES_FILE, None)
    if data is None:
        print(f"{config.ANALYSES_FILE} not found or not valid JSON")
        return 1
    if args.prune:
        data = prune(data)
        store.save_json(config.ANALYSES_FILE, data)
    problems = validate(data)
    for p in problems:
        print("problem:", p)
    if not problems:
        days = data["days"]
        print(f"ok: {len(days)} day(s), latest {days[0]['date'] if days else '-'} "
              f"with {len(days[0]['articles']) if days else 0} article(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
