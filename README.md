# Internship Tracker

A daily tracker of **capital-markets internships** (structuring, pricing, quantitative research,
model validation, market risk…) across 200+ banks, trading firms, asset managers, insurers,
institutions and consultancies.

Every morning a GitHub Actions workflow queries each employer's careers site, keeps only
internships, scores them for relevance, records what is new, and publishes a static dashboard
on GitHub Pages.

- **Today's new offers** first, sorted by relevance score
- **All offers**, filterable by employer, employer type, country, role family, date seen and score,
  with full-text search
- **Personal tracking** for each offer (status, application date, notes), stored only in the
  browser's `localStorage`, never in the repository, with CSV export / import
- Last update time and the list of employers that failed on the last run

## How it works

```
targets.yaml ──► tracker/run.py ──► adapters (one per recruitment platform)
                      │                 greenhouse · lever · smartrecruiters · workday · oracle
                      │                 successfactors · eightfold · phenom · radancy · ashby
                      │                 teamtailor · workable · recruitee · generic (HTML / JSON-LD)
                      ▼
               filters.py  (internships only: intern, stage, off-cycle, summer…;
                      │      excludes alternance / apprenticeships, VIE, spring weeks, past years)
                      ▼
               scoring.py  (role priority + geography + timing, 0–100)
                      ▼
               store.py    (dedup, history with first/last seen, open/closed status)
                      ▼
     data/jobs.json · data/new_today.json · data/errors.json ──► docs/ (static site)
```

**Adapters.** Each recruitment platform has its own module in [`tracker/adapters/`](tracker/adapters).
Public JSON APIs are preferred (Greenhouse, Lever, SmartRecruiters, Ashby, Workable, Recruitee,
the JSON endpoints behind Workday, Oracle Recruiting Cloud and Eightfold pages). HTML is only
parsed when a platform has no JSON (SuccessFactors, Radancy, Phenom, in-house sites); the generic
adapter reads schema.org `JobPosting` data first and falls back to job links.

**Politeness.** Every request carries an honest user agent pointing to this repository, requests
to a given host are spaced by at least 1.5 s (employers on different hosts run in parallel),
and `robots.txt` is checked before each request. When `robots.txt` disallows the job search,
the employer is skipped and reported, never worked around. LinkedIn and JobTeaser are excluded.

**Robustness.** Each employer is scraped in isolation: an error is logged in `data/errors.json`
and shown on the site, and the run continues. Offers of an employer that failed are not marked
as closed.

**Scoring.**

| Component | Points |
|---|---|
| Role, high priority: structuring, pricing, quantitative analyst / research, financial modelling, derivatives, model validation, XVA, market risk | 50 |
| Role, medium priority: quant developer, strats, trading, product control | 30 |
| Role, low priority: other markets roles (sales, rates, credit, equities, risk, portfolio management…) | 10 |
| Location: France / priority Europe (LU, CH, BE, UK, DE, NL, IT, ES) / other Europe / rest of world | 30 / 20 / 12 / 0 |
| Paris or London | +5 |
| Off-cycle, 6 months, 2027 | +10 / +10 / +5 |

The role is read from the title only. Offers with no markets signal at all score 0 and are dropped.

## Repository layout

| Path | Content |
|---|---|
| `targets.yaml` | Employers: platform, careers URL, adapter parameters |
| `tracker/` | Scraper (Python 3.11) |
| `tests/` | Unit tests for the filter, the score, country detection and the history merge |
| `data/` | `jobs.json` (history), `new_today.json`, `errors.json`, updated by the workflow |
| `docs/` | Static site (HTML / CSS / vanilla JS) |
| `tools/` | Platform discovery helper used when adding employers |
| `.github/workflows/` | `daily.yml` (scrape + deploy at 05:00 UTC), `discover.yml` |

## Run locally

```bash
pip install -r requirements.txt
python -m pytest -q
python -m tracker.run --dry-run                 # print what would be kept
python -m tracker.run --only "JPMorgan"         # update data/ for one employer
python -m http.server -d docs                   # then copy data/*.json to docs/data/ to preview
```

## Adding an employer

1. Find its platform. The easiest way is the discovery helper: add a line to
   [`tools/employers.yaml`](tools/employers.yaml) with the careers page, then run
   `python tools/discover.py --only "Name"` (or the *Discover platforms* workflow).
   It detects the platform (Workday, Greenhouse, Oracle, SuccessFactors…), tests the real
   adapter and reports how many internships it finds.
2. Add the employer to `targets.yaml` (or regenerate it with `python tools/build_targets.py`):

   ```yaml
   - name: Example Bank
     type: intl_bank
     platform: workday
     careers_url: https://careers.example.com
     params: {url: "https://example.wd3.myworkdayjobs.com/External"}
   ```

   The parameters of each platform are documented at the top of its adapter.
3. Check it: `python -m tracker.run --only "Example Bank" --dry-run`.

A new platform only needs a module in `tracker/adapters/` exposing
`fetch(target, http) -> list[RawJob]`, registered in `tracker/adapters/__init__.py`.

## Coverage

<!-- coverage:start -->
<!-- coverage:end -->
