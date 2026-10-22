"""Paths and global settings."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
TARGETS_FILE = ROOT / "targets.yaml"

JOBS_FILE = DATA_DIR / "jobs.json"
NEW_TODAY_FILE = DATA_DIR / "new_today.json"
ERRORS_FILE = DATA_DIR / "errors.json"

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
