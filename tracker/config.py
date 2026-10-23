"""Paths and global settings."""

from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
TARGETS_FILE = ROOT / "targets.yaml"

JOBS_FILE = DATA_DIR / "jobs.json"
NEW_TODAY_FILE = DATA_DIR / "new_today.json"
ERRORS_FILE = DATA_DIR / "errors.json"

# News watch (tracker/news)
NEWS_SOURCES_FILE = ROOT / "news_sources.yaml"
NEWS_FILE = DATA_DIR / "news.json"
MARKET_FILE = DATA_DIR / "market.json"
NEWS_ERRORS_FILE = DATA_DIR / "news_errors.json"
CALENDAR_FILE = DATA_DIR / "calendar.json"
NEWS_SUMMARY_FILE = DATA_DIR / "news_summary.json"   # optional, see tracker/news/summary.py

REPO_URL = "https://github.com/eleonoresamson3-alt/internship-tracker"
USER_AGENT = (
    "InternshipTracker/1.0 (personal job-search tool; "
    f"+{REPO_URL})"
)

# Minimum delay between two requests to the same host, in seconds.
MIN_DELAY_PER_HOST = 1.5
REQUEST_TIMEOUT = 30

# Search terms sent to platforms that support keyword search
# (Workday, Oracle, SmartRecruiters, Eightfold...). Results are merged.
# Platform searches are fuzzy ("intern" also matches "internship"), so a few
# short terms are enough.
SEARCH_TERMS = ["intern", "stage", "stagiaire", "summer", "off-cycle"]

# Employers scraped in parallel (the per-host delay still applies).
WORKERS = 8

# Safety cap on result pages fetched per search term and employer.
MAX_PAGES_PER_TERM = 10

# Offers that have not been seen for this many days are removed from history.
PRUNE_AFTER_DAYS = 45

# Offers scoring below this threshold are dropped (no capital-markets signal).
MIN_SCORE = 1

# Earliest start date possible for an internship (YYYY, MM): offers whose
# stated start is earlier are dropped. Graduation date: later starts are dropped.
EARLIEST_START = (2027, 6)
GRADUATION_YEAR = 2029
GRADUATION_MONTH = 6


def year_window(today: date | None = None) -> tuple[int, int]:
    """Start years worth tracking: from now until graduation.

    The window moves by itself: from September on, internships of the current
    year have started already, so the window begins the following year.
    """
    today = today or date.today()
    first = today.year + 1 if today.month >= 9 else today.year
    return max(first, EARLIEST_START[0]), GRADUATION_YEAR


def starts_too_early(year: int, month: int, today: date | None = None) -> bool:
    """True when a known start month is before EARLIEST_START (or already past)."""
    today = today or date.today()
    earliest = max(EARLIEST_START, (today.year, today.month))
    return (year, month) < earliest
