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
- **Offers added by hand** (found elsewhere: forums, network, uncovered sites), editable and
  deletable, with a status summary of all applications
- **Companies** tab: every employer of the list (scraped or not) with its careers page, the usual
  application windows for its type (indicative), a contact status, and a **priority score**
  (employer type, structuring/pricing specialists and location from `tracker/company_score.py`,
  plus open window, current relevant offers and contact status on the site)
- Filters on timing (start in June, summer, off-cycle) and start year
- **Deadlines**: read from the ad when stated ("Application deadline: 15 November 2026"),
  otherwise estimated from the usual recruiting calendar of the employer type; an "À ne pas
  rater" panel lists closings within 14 days, and a **daily e-mail digest** is sent through a
  GitHub issue comment that mentions the repository owner (`tracker/notify.py`)
- Offers that are gone (removed by the employer, or past a stated deadline) disappear by
  themselves, except those already applied to, which stay in *Mon suivi*
- Last update time and the list of employers that failed on the last run
- **Actualité** tab: a daily financial news watch for interview preparation (see
  [News watch](#news-watch-actualité-tab))

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
| Role, medium priority: quant developer, strats, trading / front office, product control, hedging (FX, rates, commodities) | 30 |
| Role, low priority: other markets roles (sales, rates, credit, equities, risk, portfolio management…) | 10 |
| Location: France / priority Europe (LU, CH, BE, UK, DE, NL, IT, ES) / other Europe / rest of world | 30 / 20 / 12 / 0 |
| Paris or London | +5 |
| Start in June / other summer internship / off-cycle | +15 / +12 / +6 |
| 6-month internship | +5 |

The role is read from the title only. Offers with no markets signal at all score 0 and are dropped.
For large corporates (type `corporate`: Airbus, Air Liquide, Pernod Ricard, Thales...), only titles
naming a markets activity are kept (treasury, hedging, FX, commodities, financing, front office...),
since these groups post many unrelated finance internships (controlling, audit, accounting).

**Timing.** [`tracker/timing.py`](tracker/timing.py) reads the start month and year from the title
("Stage – Structuration – Juin 2027") and, when the platform provides it, from the description
("start date: January 2027", "début du stage : septembre 2027", "ab Juni 2027"), and labels each
offer *summer*, *off-cycle* or *unknown*. Only internships starting between the earliest possible
start and graduation are kept: set `EARLIEST_START` (June 2027) and `GRADUATION_YEAR` (2029) in
[`tracker/config.py`](tracker/config.py). An offer whose stated start month is earlier
("Stage – Mars 2027") is dropped; an offer with only a year ("Off-cycle 2027") is kept. Offers with no date stay in the list, labelled
"Calendrier inconnu".

## News watch (*Actualité* tab)

A second module, run by the same daily workflow (separate step: a news problem never blocks the
internship tracker), prepares about ten minutes of reading for pricing / structuring interviews.

```
news_sources.yaml ──► tracker/news/run.py ──► feeds.py     (RSS / Atom, PoliteClient, robots.txt)
                                │              classify.py  (9 themes, FR + EN keywords, score 0–100)
                                │              dedupe.py    (same story across sources, 30-day history)
                                │              market.py    (ECB, Bundesbank, FRED)
                                │              calendar.py  (ECB and Fed meeting dates)
                                ▼
   data/news.json · market.json · calendar.json · news_errors.json ──► Actualité tab
   tracker/news/summary.py (optional) ──► data/news_summary.json
```

**On the site.**

- Market banner: level and 1-day / 1-week / 1-month change (in % for prices, in basis points for
  rates), green / red. A series that cannot be obtained legally and for free shows *indisponible*
  with the reason as a tooltip; nothing is ever estimated.
- Next ECB and Fed monetary policy meetings.
- *Aujourd'hui*: the optional summary, the 10 most important articles of the last 24 hours, then
  all of them with search and theme / source filters.
- *Semaine*: the important articles (score ≥ 30) of the last 7 days grouped by main theme.
- *À retenir*: articles marked with ☆, with CSV export. "Lu" and "à retenir" marks are stored in
  the browser's `localStorage` only (key `internship-tracker.v1.news`), never in the repository.
- Sources or market series that failed on the last run are listed discreetly under the banner.

**Themes and score** ([`tracker/news/classify.py`](tracker/news/classify.py)). Keywords in French
and English, accents and case ignored, title counted twice. Score = weight of the main theme + half
of the second theme's + 10 for an official source + 15 per additional source covering the same
story (at most +30), capped at 100.

| Theme | Weight |
|---|---|
| Central banks and rates; volatility and derivatives; structured products | 40 |
| Credit and sovereign debt | 25 |
| FX and commodities; macro and inflation; regulation | 20 |
| Equity markets; banks and financial sector | 15 |
| No theme | 5 |

**Deduplication** ([`tracker/news/dedupe.py`](tracker/news/dedupe.py)). Two titles are the same
story when they share at least 3 significant words and 60 % of the shorter title's significant
words; the story keeps every source that covered it. History: 30 days in `data/news.json`, and
the whole history is re-classified on each run.

### Sources

Only public, free RSS feeds are used: headlines, publication time and the publisher's own RSS
abstract, with a link to the original article. `robots.txt` is checked before every request.
Feeds are tested on each run; a failing feed is logged and the others continue. A feed whose
newest item is more than 14 days old is reported as *stale*.

| Source | Feed | Type |
|---|---|---|
| ECB (press releases, blog) | `ecb.europa.eu/rss/press.html`, `/rss/blog.html` | official |
| Federal Reserve | `federalreserve.gov/feeds/press_all.xml` | official |
| Bank of England | `bankofengland.co.uk/rss/news` | official |
| BIS | `bis.org/doclist/all_pressrels.rss` | official |
| AMF | `amf-france.org/fr/flux-rss/display/23` | official |
| L'Agefi | `agefi.fr/index.rss` | press |
| Financial Times (Markets, Global economy) | `ft.com/markets?format=rss`, `/global-economy?format=rss` | press |
| MarketWatch Top Stories (Dow Jones public feed) | `feeds.content.dowjones.io/public/rss/mw_topstories` | press |
| Investing.com France | `fr.investing.com/rss/news.rss` | press |
| Le Monde – Économie | `lemonde.fr/economie/rss_full.xml` | press |

Tested and rejected:

| Source | Reason |
|---|---|
| Les Echos | every feed (`services.lesechos.fr/rss/...`, `lesechos.fr/rss`) answers 403 Forbidden to scripts |
| Reuters | no public RSS feed since 2020 |
| Banque de France | no RSS feed found (`/rss`, `/rss.xml`: 403 / 404); press releases are only an HTML page |
| IMF | the RSS URLs (`imf.org/en/News/RSS`, `external/rss/feeds.aspx`) return 404 or an HTML page |
| CNBC | `robots.txt` disallows its RSS search endpoint |
| ESMA, Zonebourse | 403 Forbidden |
| Boursorama, La Tribune | no RSS at the tested URLs (404) |
| Risk.net | no public feed (404), and paid content |
| MarketWatch Market Pulse | the feed answers but is frozen (newest item from July 2025) |

Paid content (FT, L'Agefi) is only linked: log in on the publisher's site with your own account
(an ENSAE / HEC subscription works) to read full articles. No credential is ever stored here.

### Market data

Free official sources, no API key: ECB Data Portal (EUR/USD reference rate, €STR, deposit
facility rate), Deutsche Bundesbank (German 2-year and 10-year yields from the yield curve), FRED
of the St. Louis Fed (S&P 500, Nasdaq Composite, Dow Jones, Nikkei 225, VIX, Brent, US 2-year and 10-year Treasury yields). Each series is
configured in `news_sources.yaml`.

| Series | Status | Why |
|---|---|---|
| CAC 40 | *indisponible* | Euronext data is licensed; the Banque de France Webstat series (`ECOFI.SPI.FR.FPE_IX._Z.D`) stopped in July 2024 |
| Euro Stoxx 50, VSTOXX | *indisponible* | STOXX indices are licensed; the ECB no longer publishes them |
| Gold | monthly average only | the daily LBMA price is licensed and FRED no longer distributes it; the World Bank *Pink Sheet* (CC BY 4.0) publishes a free monthly average, shown with its month and its 1-month change |
| France 2-year and 10-year | from Banque de France Webstat (TEC 2, TEC 10) when the `WEBSTAT_API_KEY` secret is set | the Webstat API is free but needs a personal API key (see below) |

FRED and some official series are published with a delay of one business day; each tile shows
the date of its last value.

**French yields (Banque de France Webstat).** Create a free account on
[webstat.banque-france.fr](https://webstat.banque-france.fr/), generate an API key in the account
settings, then add it as a repository secret: *Settings → Secrets and variables → Actions → New
repository secret*, name `WEBSTAT_API_KEY`. Never paste the key in a file, an issue or a chat.
Without the secret the two tiles show *indisponible*. Series keys are set in `news_sources.yaml`
(daily constant-maturity rates *TEC 2* and *TEC 10*: `FM.D.FR.EUR.FR2.BB.FRMOYTEC2.HSTA`, `...FRMOYTEC10.HSTA`); if Webstat answers with no data, the
error shown on the site lists similar keys.

Without any account, the ECB and FRED only publish a *monthly* French 10-year yield, which is why
it is not used for the daily banner.

### Central bank calendar

[`tracker/news/calendar.py`](tracker/news/calendar.py) reads the ECB Governing Council calendar
and the Fed FOMC calendar from their official pages. If a page cannot be read, the manual list
`calendar_manual` in `news_sources.yaml` is used for that bank (copied from the same official
pages; update it once a year).

### Morning analyses (scheduled Claude Code session)

Every morning, after *Daily scrape*, a scheduled Claude Code task (created from Claude Code on
the web, running on the owner's Claude subscription, so no API bill) opens a session on this
repository and follows [`ANALYSES.md`](ANALYSES.md): it reads `data/news.json`, `market.json` and
`calendar.json` and writes 3 to 5 short explanatory articles in French — what happened, why it
matters, the impact on rates, volatility, FX, credit and structured products, a likely interview
question with answer hints, a small glossary and the sources — plus a one-minute brief.

```
scheduled session ──► data/analyses.json on branch claude/analyses
                         └─► .github/workflows/analyses.yml: python -m tracker.news.analyses --check,
                             copy to main, then Daily scrape with site_only=true (deploy only)
```

They appear in the *Analyses* view of the *Actualité* tab (opened by default when they are
recent), with a selector for the previous days (30 days kept). The site labels them as generated
and to be checked against the sources. The session's instructions are versioned in `ANALYSES.md`:
edit that file to change the tone, length or topics. The scheduled task itself is managed from
Claude Code (claude.ai/code → scheduled tasks); it uses the subscription's usage limits.

### Optional daily summary through the API (off by default)

[`tracker/news/summary.py`](tracker/news/summary.py) runs only if the repository has an
`ANTHROPIC_API_KEY` secret. It sends the headlines and RSS abstracts of the last 24 hours (top 40)
and of the rest of the week (top 30) to the Anthropic API and shows on the site a French summary
of about 200 words (5 facts and what they imply for rates, volatility and structured products)
and 3 possible interview questions. The model is told to use only the headlines provided; the
site labels the text as generated and to be checked against the articles.

- **Turn it on:** create an API key at console.anthropic.com (with a payment method), then
  *Settings → Secrets and variables → Actions → New repository secret*, name `ANTHROPIC_API_KEY`.
  Delete the secret to turn it off.
- **Cost:** model `claude-opus-5-5`, $4 per million input tokens and $20 per million output
  tokens. One call per day of about 3,000–6,000 input tokens and 1,000–3,000 output tokens
  (thinking included) costs about $0.03–0.08 per day, i.e. **about $1–2.5 per month**. Changing
  `MODEL` to `claude-haiku-5-5` ($0.10 / $0.50 per million tokens) would cost a few cents per
  month, with a less thorough summary. Setting a monthly spend limit in the Anthropic console is
  recommended.
- **Server-side fallback:** the call enables the API's server-side fallback, so a request declined
  by a safety classifier is retried on a fallback model instead of failing.
- If the call fails, nothing is written and the site simply shows no summary.

## Repository layout

| Path | Content |
|---|---|
| `targets.yaml` | Employers: platform, careers URL, adapter parameters |
| `news_sources.yaml` | News feeds, market series and the manual central bank calendar |
| `tracker/` | Scraper (Python 3.11); `tracker/news/` is the news watch |
| `tests/` | Unit tests for the filter, the score, country detection, the history merge, news classification, deduplication and calendar parsing |
| `data/` | `jobs.json` (history), `new_today.json`, `errors.json`, and the news files (`news.json`, `market.json`, `calendar.json`, `news_errors.json`, `analyses.json`, optional `news_summary.json`), updated by the workflow |
| `docs/` | Static site (HTML / CSS / vanilla JS); `docs/employers.json` is generated by `tools/build_targets.py` |
| `tools/` | `discover.py` (detects and tests each employer's platform), `employers.yaml` (its input), `build_targets.py` + `overrides.yaml` (generate `targets.yaml`) |
| `.github/workflows/` | `daily.yml` (scrape + deploy at 05:00 UTC; `site_only` input to only redeploy), `analyses.yml` (publishes the morning analyses), `discover.yml` |
| `ANALYSES.md` | Instructions followed by the scheduled Claude Code session that writes the morning analyses |

## Run locally

```bash
pip install -r requirements.txt
python -m pytest -q
python -m tracker.run --dry-run                 # print what would be kept
python -m tracker.run --only "JPMorgan"         # update data/ for one employer
python -m tracker.news.run                      # news, market data and calendar (--all also tries disabled feeds)
python -m http.server -d docs                   # then copy data/*.json to docs/data/ to preview
```

## Adding an employer

1. Find its platform. The easiest way is the discovery helper: add a line to
   [`tools/employers.yaml`](tools/employers.yaml) with the careers page, then run
   `python tools/discover.py --only "Name"` (or the *Discover platforms* workflow).
   It detects the platform (Workday, Greenhouse, Oracle, SuccessFactors…), tests the real
   adapter and reports how many internships it finds.
2. Add the employer to `targets.yaml`, either by hand or by regenerating it from the discovery
   results with `python tools/build_targets.py` (manual fixes go in `tools/overrides.yaml`):

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

## GitHub setup

1. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
2. **Settings → Actions → General → Workflow permissions: Read and write permissions**
   (the workflow commits `data/`; the workflow file also requests `contents: write` itself).
3. **Actions tab → Daily scrape → Run workflow** once, to publish the site immediately.
   It then runs every day at 05:00 UTC. The site is served at
   `https://<user>.github.io/internship-tracker/`.

GitHub may disable scheduled workflows on repositories without activity for 60 days; if that
happens, re-enable *Daily scrape* from the Actions tab.

## Coverage

<!-- coverage:start -->
143 of 392 employers are scraped daily.

| Employer | Platform |
|---|---|
| AB InBev | greenhouse |
| Aberdeen | workday |
| Accenture | workday |
| Air Liquide | workday |
| Airbus | workday |
| Akuna Capital | greenhouse |
| AllianceBernstein | workday |
| Allianz | phenom |
| Alstom | successfactors |
| Amundi | generic |
| AQR | greenhouse |
| Arrowstreet Capital | workday |
| Aviva Investors | workday |
| B2C2 | greenhouse |
| Bank of America | generic |
| Bank of England | oracle |
| Banque de France | workday |
| Barclays | workday |
| BBVA | workday |
| BCE (ECB) | generic |
| BearingPoint | teamtailor |
| Belvedere Trading | lever |
| BlackRock | workday |
| Bloomberg | generic |
| BMO Capital Markets | phenom |
| BNY | oracle |
| Brevan Howard | phenom |
| CaixaBank | successfactors |
| Capco | greenhouse |
| Capital Group | workday |
| Capstone Investment Advisors | greenhouse |
| Cboe | phenom |
| Citi | workday |
| Clear Street | greenhouse |
| CME Group | workday |
| Commonwealth Bank | workday |
| Da Vinci | greenhouse |
| Daiwa | teamtailor |
| Deloitte | generic |
| Deutsche Bank | workday |
| Diageo | workday |
| DRW | greenhouse |
| DZ Bank | successfactors |
| Eclipse Trading | greenhouse |
| EDF Trading | workday |
| Engineers Gate | greenhouse |
| Euroclear | oracle |
| Euronext | workday |
| ExodusPoint | greenhouse |
| EY | successfactors |
| FCA | workday |
| Fidelity International | workday |
| Five Rings | greenhouse |
| Flow Traders | greenhouse |
| Flowdesk | greenhouse |
| Forvis Mazars | greenhouse |
| Franklin Templeton | phenom |
| Garda Capital | greenhouse |
| Grant Thornton | recruitee |
| Groupe Crédit Agricole | generic |
| GSR | greenhouse |
| Gunvor | workday |
| Headlands Technologies | greenhouse |
| Hudson River Trading | greenhouse |
| IMC | greenhouse |
| Invesco | workday |
| Jane Street | greenhouse |
| Jefferies | generic |
| JPMorgan | oracle |
| Jump Trading | greenhouse |
| Kepler Cheuvreux | teamtailor |
| Kering | workday |
| Keyrock | ashby |
| KPMG | radancy |
| Lazard | oracle |
| Lloyds Banking Group | workday |
| Lombard Odier | workday |
| LSEG | workday |
| LVMH | recruitee |
| Lynx Asset Management | teamtailor |
| M&G | workday |
| Macquarie | generic |
| Mako | greenhouse |
| Man Group | greenhouse |
| Marshall Wace | greenhouse |
| Maven Securities | greenhouse |
| Michelin | workday |
| Mizuho | workday |
| Morgan Stanley | workday |
| MUFG | workday |
| Murex | workday |
| Muzinich | workday |
| Nasdaq (Calypso / Adenza) | workday |
| Nomura | generic |
| Northern Trust | workday |
| Novartis | workday |
| Numerix | greenhouse |
| Optiver | greenhouse |
| Orange | phenom |
| Paradigm | ashby |
| PDT Partners | greenhouse |
| Pernod Ricard | workday |
| Philips | workday |
| PIMCO | workday |
| Point72 | greenhouse |
| PwC | workday |
| Quadrature Capital | greenhouse |
| Quanteam | generic |
| Qube Research & Technologies | greenhouse |
| Radix Trading | greenhouse |
| Raiffeisen Bank International | successfactors |
| RBC Capital Markets | workday |
| Rothschild & Co | generic |
| S&P Global | workday |
| Sanofi | workday |
| Santander CIB | workday |
| Schonfeld | greenhouse |
| Schroders | oracle |
| SCOR | oracle |
| Scotiabank | successfactors |
| Shell Trading | workday |
| Siemens | generic |
| Squarepoint | greenhouse |
| State Street | workday |
| Stifel | generic |
| T. Rowe Price | workday |
| TD Securities | workday |
| Thales | workday |
| Tower Research | greenhouse |
| Trafigura | workday |
| UniCredit | generic |
| Unilever | workday |
| Virtu Financial | greenhouse |
| Voleon | ashby |
| Volkswagen Financial Services | successfactors |
| Vontobel | workday |
| Wellington Management | workday |
| Wintermute | lever |
| Winton | greenhouse |
| WorldQuant | greenhouse |
| XTX Markets | greenhouse |
| Zanders | teamtailor |
| Zurich | successfactors |

**Not covered yet**, with the reason:

| Employer | Reason |
|---|---|
| ABB | uses phenom, which has no public job API supported yet |
| ABN AMRO | careers site not reachable by a script (HTTPError: 503 Server Error: Service Unavailable for url: https://www.abnamro.co) |
| Accuracy | robots.txt disallows automated access to the careers pages |
| ACPR | in-house careers site with no machine-readable job list found |
| Aequam Capital | careers site not reachable by a script (ConnectionError: HTTPSConnectionPool(host='www.aequamcapital.com', port=443): Ma) |
| Agence France Trésor | in-house careers site with no machine-readable job list found |
| Ailancy | uses welcometothejungle, which has no public job API supported yet |
| Air France-KLM | careers site not reachable by a script (ReadTimeout: HTTPSConnectionPool(host='www.airfrance.fr', port=443): Read timed ) |
| All Options | careers site not reachable by a script (ConnectionError: ('Connection aborted.', RemoteDisconnected('Remote end closed c) |
| Allianz GI | covered by the Allianz entry (careers.allianz.com lists all Allianz companies, including Allianz Global Investors). |
| Alpiq | careers site blocks automated requests (HTTP 403) |
| Alvarez & Marsal | careers site blocks automated requests (HTTP 403) |
| AMF | robots.txt disallows automated access to the careers pages |
| Amundi Luxembourg | covered by the Amundi entry (jobs.amundi.com lists all Amundi entities, including Luxembourg). |
| Aon | the Teamtailor site found is empty; jobs.aon.com has no machine-readable job list supported yet. |
| ASML | in-house careers site with no machine-readable job list found |
| Aspect Capital | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.aspectcapital.com/ca) |
| Avantage Reply | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.reply.com/en/careers) |
| AXA | candidate platforms failed (HTTPError: 403 Client Error: Forbidden for url: https://recrutement.axa.fr/searc) |
| AXA IM | careers site blocks automated requests (HTTP 403) |
| AXA XL | uses cornerstone, which has no public job API supported yet |
| Axpo | uses teamtailor, which has no public job API supported yet |
| Balyasny | in-house careers site with no machine-readable job list found |
| Banco Sabadell | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.grupbancsabadell.com) |
| Bankinter | in-house careers site with no machine-readable job list found |
| Banque Cantonale de Genève | in-house careers site with no machine-readable job list found |
| Banque Cantonale Vaudoise | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.bcv.ch/fr/la-bcv/emp) |
| Banque centrale du Luxembourg | in-house careers site with no machine-readable job list found |
| Banque de Luxembourg | in-house careers site with no machine-readable job list found |
| Banque Internationale à Luxembourg | in-house careers site with no machine-readable job list found |
| Banque mondiale | uses cornerstone, which has no public job API supported yet |
| Banque Syz | in-house careers site with no machine-readable job list found |
| BayernLB | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.bayernlb.com/interne) |
| Beacon Platform | in-house careers site with no machine-readable job list found |
| BEI (EIB) | robots.txt disallows automated access to the careers pages |
| Belfius | careers site not reachable by a script (HTTPError: 500 Server Error: Internal Server Error for url: https://www.belfius.) |
| BGC Group | careers site blocks automated requests (HTTP 403) |
| BGL BNP Paribas | in-house careers site with no machine-readable job list found |
| BlueCrest | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.bluecrestcapital.com) |
| BNP Paribas | candidate platforms failed (HTTPError: 403 Client Error: Forbidden for url: https://group.bnpparibas/en/care) |
| BNP Paribas AM | careers site blocks automated requests (HTTP 403) |
| BNP Paribas Cardif | in-house careers site with no machine-readable job list found |
| BNP Paribas Fortis | careers site not reachable by a script (HTTPError: 503 Server Error: Service Unavailable for url: https://www.bnpparibas) |
| BNS (SNB) | uses successfactors, which has no public job API supported yet |
| Bouygues | careers site blocks automated requests (HTTP 403) |
| BP (corporate treasury) | careers site blocks automated requests (HTTP 403) |
| BP Trading | careers site blocks automated requests (HTTP 403) |
| Bpifrance | careers site blocks automated requests (HTTP 403) |
| BRED | in-house careers site with no machine-readable job list found |
| BRI (BIS) | in-house careers site with no machine-readable job list found |
| Bundesbank | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.bundesbank.de/en/bun) |
| CACEIS | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.caceis.com/careers/) |
| Caisse des Dépôts | in-house careers site with no machine-readable job list found |
| Candriam | in-house careers site with no machine-readable job list found |
| Cantor Fitzgerald | careers site blocks automated requests (HTTP 403) |
| Capgemini | robots.txt disallows automated access to the careers pages |
| Capgemini Invent | robots.txt disallows automated access to the careers pages |
| Capula | careers site not reachable by a script (HTTPError: 429 Client Error: Too Many Requests for url: https://apply.workable.c) |
| Cargill | robots.txt disallows automated access to its job search |
| Carmignac | in-house careers site with no machine-readable job list found |
| Carrefour | careers site blocks automated requests (HTTP 403) |
| Castleton Commodities | candidate platforms failed (HTTPError: 422 Client Error: Unprocessable Entity for url: https://osv-cci.wd1.m) |
| Caxton Associates | uses workable, which has no public job API supported yet |
| Centrica Energy Trading | in-house careers site with no machine-readable job list found |
| CFM | the Greenhouse board "cfm" belongs to another company; cfm.com publishes no machine-readable job list. |
| Chappuis Halder & Co | careers site not reachable by a script (SSLError: HTTPSConnectionPool(host='www.chappuishalder.com', port=443): Max retr) |
| CIC Market Solutions | robots.txt disallows automated access to the careers pages |
| Citadel | careers site blocks automated requests (HTTP 403) |
| Citadel Securities | careers site blocks automated requests (HTTP 403) |
| CNP Assurances | robots.txt disallows automated access to the careers pages |
| Columbia Threadneedle | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.columbiathreadneedle) |
| Comgest | careers site not reachable by a script (HTTPError: 404 Client Error: Page not found for url: https://www.comgest.com/en/) |
| Commerzbank | robots.txt disallows automated access to the careers pages |
| Covéa | robots.txt disallows automated access to its job search |
| Crédit Agricole Indosuez | covered by the Groupe Crédit Agricole entry (groupecreditagricole.jobs lists all group entities). |
| Crédit Mutuel Arkéa | careers site not reachable by a script (HTTPError: 400 Client Error:  for url: https://www.cm-arkea.com/arkea/banque/ass) |
| d-fine | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.d-fine.com/en/career) |
| D. E. Shaw | in-house careers site with no machine-readable job list found |
| Danone | robots.txt disallows automated access to the careers pages |
| Danske Bank | robots.txt disallows automated access to the careers pages |
| Danske Commodities | in-house careers site with no machine-readable job list found |
| Dassault Systèmes | robots.txt disallows automated access to the careers pages |
| De Nederlandsche Bank | in-house careers site with no machine-readable job list found |
| Degroof Petercam | in-house careers site with no machine-readable job list found |
| DekaBank | uses successfactors, which has no public job API supported yet |
| Deribit | uses recruitee, which has no public job API supported yet |
| Deutsche Börse / Eurex | the only Workday site found belongs to ISS (a subsidiary), not to Deutsche Börse / Eurex; careers site is in-house. |
| DNB | the Lever board "dnb" belongs to Dun & Bradstreet, not to DNB bank; dnb.no careers is in-house. |
| DNCA Finance | in-house careers site with no machine-readable job list found |
| EBA | careers site blocks automated requests (HTTP 403) |
| EDF | careers site blocks automated requests (HTTP 403) |
| Edmond de Rothschild | candidate platforms failed (ConnectionError: HTTPSConnectionPool(host='fa-evht-saasfaprod1.fa.ocs.oracleclou) |
| EFG International | careers site blocks automated requests (HTTP 403) |
| Eisler Capital | careers site not reachable by a script (ConnectionError: HTTPSConnectionPool(host='www.eislercapital.com', port=443): Ma) |
| Eleva Capital | robots.txt disallows automated access to the careers pages |
| EnBW | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.enbw.com/careers/) |
| Engie GEMS | robots.txt disallows automated access to its job search |
| Equita | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.equita.eu/en/careers) |
| Erste Group | in-house careers site with no machine-readable job list found |
| ESMA | careers site blocks automated requests (HTTP 403) |
| Exane (BNP Paribas) | careers site not reachable by a script (ReadTimeout: HTTPSConnectionPool(host='www.exane.com', port=443): Read timed out) |
| Exton Consulting | careers site not reachable by a script (ConnectionError: HTTPSConnectionPool(host='www.extonconsulting.com', port=443): ) |
| FactSet | candidate platforms failed (HTTPError: 422 Client Error: Unprocessable Entity for url: https://factset.wd1.m) |
| Fasanara Capital | uses workable, which has no public job API supported yet |
| FEI (EIF) | in-house careers site with no machine-readable job list found |
| Finalyse | in-house careers site with no machine-readable job list found |
| Finastra | candidate platforms failed (HTTPError: 404 Client Error: Not Found for url: https://finastra.wd3.myworkdayjo) |
| Fintegral | uses teamtailor, which has no public job API supported yet |
| Fitch Ratings | candidate platforms failed (HTTPError: 422 Client Error: Unprocessable Entity for url: https://fitch.wd1.myw) |
| FMI (IMF) | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.imf.org/en/Careers) |
| Fourpoints IM | in-house careers site with no machine-readable job list found |
| G-Research | robots.txt disallows automated access to the careers pages |
| Generali | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.generali.com/careers) |
| Generali Investments | in-house careers site with no machine-readable job list found |
| Glencore | in-house careers site with no machine-readable job list found |
| Global Trading Systems | careers site not reachable by a script (ConnectionError: HTTPSConnectionPool(host='www.gts.com', port=443): Max retries ) |
| Goldman Sachs | uses avature, which has no public job API supported yet |
| Graham Capital | in-house careers site with no machine-readable job list found |
| Groupama AM | in-house careers site with no machine-readable job list found |
| H2O AM | careers site not reachable by a script (ConnectionError: HTTPSConnectionPool(host='careers.h2o-am.com', port=443): Max r) |
| Handelsbanken | robots.txt disallows automated access to the careers pages |
| Hannover Re | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.hannover-re.com/care) |
| Hartree Partners | careers site blocks automated requests (HTTP 403) |
| Heineken | careers site not reachable by a script (ReadTimeout: HTTPSConnectionPool(host='careers.theheinekencompany.com', port=443) |
| Helaba | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.helaba.com/int/caree) |
| Hermès | careers site blocks automated requests (HTTP 403) |
| HSBC | robots.txt disallows automated access to the careers pages |
| HSBC Continental Europe | robots.txt disallows automated access to the careers pages |
| Hutchin Hill | careers site not reachable by a script (SSLError: HTTPSConnectionPool(host='www.hutchinhill.com', port=443): Max retries) |
| ICE | candidate platforms failed (HTTPError: 422 Client Error: Unprocessable Entity for url: https://intercontinen) |
| ING | robots.txt disallows automated access to its job search |
| Insight Investment | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.insightinvestment.co) |
| Intesa Sanpaolo | in-house careers site with no machine-readable job list found |
| Investec | candidate platforms failed (HTTPError: 422 Client Error: Unprocessable Entity for url: https://investec.wd3.) |
| ION Group | in-house careers site with no machine-readable job list found |
| J. Safra Sarasin | in-house careers site with no machine-readable job list found |
| Janus Henderson | candidate platforms failed (HTTPError: 422 Client Error: Unprocessable Entity for url: https://janushenderso) |
| Julius Baer | careers site blocks automated requests (HTTP 403) |
| Kaiko | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.kaiko.com/careers) |
| KBC | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.kbc.com/en/careers.h) |
| KfW | jobs.kfw.de exposes no list of offers that can be read automatically. |
| L'Oréal | robots.txt disallows automated access to its job search |
| La Banque Postale | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.labanquepostale.com/) |
| La Financière de l'Echiquier | in-house careers site with no machine-readable job list found |
| La Française | in-house careers site with no machine-readable job list found |
| Lazard Frères Gestion | careers site not reachable by a script (SSLError: HTTPSConnectionPool(host='www.lazardfreresgestion.fr', port=443): Max ) |
| LBBW | careers site not reachable by a script (ConnectionError: ('Connection aborted.', ConnectionResetError(104, 'Connection r) |
| Legal & General | careers site not reachable by a script (ConnectionError: HTTPSConnectionPool(host='www.legalandgeneralgroup.com', port=4) |
| Leonteq | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.leonteq.com/company/) |
| LGT | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.lgt.com/global-en/ca) |
| Liquid Capital | careers site not reachable by a script (ConnectionError: HTTPSConnectionPool(host='www.liquidcapital.com', port=443): Ma) |
| LMR Partners | in-house careers site with no machine-readable job list found |
| Louis Dreyfus Company | careers site blocks automated requests (HTTP 403) |
| Lucht Probst Associates | in-house careers site with no machine-readable job list found |
| Marex | careers site not reachable by a script (ConnectionError: HTTPConnectionPool(host='www.marex.test', port=80): Max retries) |
| MarketAxess | in-house careers site with no machine-readable job list found |
| Mediobanca | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.mediobanca.com/en/ca) |
| Mercuria | careers site not reachable by a script (SSLError: HTTPSConnectionPool(host='mercuria.com', port=443): Max retries exceed) |
| MES (ESM) | robots.txt disallows automated access to the careers pages |
| Millennium | robots.txt disallows automated access to its job search |
| Milliman | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.milliman.com/en/care) |
| Mint Tower | careers site not reachable by a script (ConnectionError: HTTPSConnectionPool(host='www.minttowercapital.comcareers', por) |
| Mirabaud | in-house careers site with no machine-readable job list found |
| Mirova | in-house careers site with no machine-readable job list found |
| Mobilize Financial Services (RCI Bank) | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.mobilize-fs.com/care) |
| Moneta AM | in-house careers site with no machine-readable job list found |
| Moody's | robots.txt disallows automated access to its job search |
| MSCI | candidate platforms failed (HTTPError: 401 Client Error: Unauthorized for url: https://msci.wd1.myworkdayjob) |
| Munich Re | robots.txt disallows automated access to its job search |
| National Bank of Canada | robots.txt disallows automated access to the careers pages |
| Natixis CIB | in-house careers site with no machine-readable job list found |
| Natixis IM | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.im.natixis.com/en-in) |
| NatWest Markets | careers site blocks automated requests (HTTP 403) |
| Nestlé | careers site blocks automated requests (HTTP 403) |
| Ninety One | robots.txt disallows automated access to the careers pages |
| NORD/LB | robots.txt disallows automated access to the careers pages |
| Nordea | the Teamtailor site found is empty / not Nordea's main careers site; nordea.com careers is in-house. |
| Nuveen | in-house careers site with no machine-readable job list found |
| Nyenburgh | careers site not reachable by a script (SSLError: HTTPSConnectionPool(host='www.nyenburgh.com', port=443): Max retries e) |
| Oddo BHF | in-house careers site with no machine-readable job list found |
| Ofi Invest | in-house careers site with no machine-readable job list found |
| Old Mission | uses ashby, which has no public job API supported yet |
| OpenGamma | in-house careers site with no machine-readable job list found |
| Opensee | uses welcometothejungle, which has no public job API supported yet |
| Orchestrade | in-house careers site with no machine-readable job list found |
| Ossiam | in-house careers site with no machine-readable job list found |
| Ostrum | in-house careers site with no machine-readable job list found |
| PartnerRe | uses successfactors, which has no public job API supported yet |
| Peak6 | in-house careers site with no machine-readable job list found |
| Pictet | uses successfactors, which has no public job API supported yet |
| Quantifi | in-house careers site with no machine-readable job list found |
| Quantitative Brokers | in-house careers site with no machine-readable job list found |
| Quintet Private Bank | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.quintet.com/en-gb/ca) |
| Rabobank | careers site blocks automated requests (HTTP 403) |
| Renault Group | in-house careers site with no machine-readable job list found |
| Robeco | in-house careers site with no machine-readable job list found |
| Roche | uses phenom, which has no public job API supported yet |
| Rokos Capital | in-house careers site with no machine-readable job list found |
| RWE Supply & Trading | in-house careers site with no machine-readable job list found |
| Safran | careers site blocks automated requests (HTTP 403) |
| Saint-Gobain | careers site blocks automated requests (HTTP 403) |
| Schneider Electric | in-house careers site with no machine-readable job list found |
| SEB | in-house careers site with no machine-readable job list found |
| Seeyond | in-house careers site with no machine-readable job list found |
| Sia Partners | robots.txt disallows automated access to its job search |
| Sienna IM | robots.txt disallows automated access to its job search |
| SimCorp | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.simcorp.com/careers) |
| SIX Group | candidate platforms failed (HTTPError: 404 Client Error: Not Found for url: https://www.six-group.com/search) |
| SMBC | uses successfactors, which has no public job API supported yet |
| Société Générale | careers.societegenerale.com renders its search in JavaScript and exposes no public job endpoint (Taleo back-office is not public). |
| Société Générale Luxembourg | in-house careers site with no machine-readable job list found |
| Spuerkeess (BCEE) | uses cornerstone, which has no public job API supported yet |
| Square Management | in-house careers site with no machine-readable job list found |
| Standard Chartered | robots.txt disallows automated access to its job search |
| Statkraft | robots.txt disallows automated access to its job search |
| Stellantis | candidate platforms failed (HTTPError: 404 Client Error: Not Found for url: https://stellantis.wd3.myworkday) |
| Susquehanna (SIG) | robots.txt disallows automated access to its job search |
| Swedbank | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.swedbank.com/about-s) |
| Swiss Life AM | careers site blocks automated requests (HTTP 403) |
| Swiss Re | candidate platforms failed (HTTPError: 404 Client Error: Not Found for url: https://www.swissre.com/search/?) |
| Swissquote | robots.txt disallows automated access to its job search |
| Sycomore AM | robots.txt disallows automated access to its job search |
| Syquant Capital | careers site not reachable by a script (ConnectionError: HTTPSConnectionPool(host='www.syquant.com', port=443): Max retr) |
| Systematica Investments | in-house careers site with no machine-readable job list found |
| Tibra | uses workable, which has no public job API supported yet |
| Tikehau Capital | in-house careers site with no machine-readable job list found |
| TOBAM | in-house careers site with no machine-readable job list found |
| TotalEnergies Trading | robots.txt disallows automated access to the careers pages |
| TP ICAP | careers site not reachable by a script (SSLError: HTTPSConnectionPool(host='www.tpicap.com', port=443): Max retries exce) |
| Tradeweb | in-house careers site with no machine-readable job list found |
| Tradition | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.trad-x.com/news/2014) |
| Two Sigma | in-house careers site with no machine-readable job list found |
| UBS | candidate platforms failed (HTTPError: 404 Client Error: Not Found for url: https://www.ubs.com/search-jobs/) |
| Unigestion | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://unigestion.com/careers) |
| Union Bancaire Privée | in-house careers site with no machine-readable job list found |
| Uniper | careers site blocks automated requests (HTTP 403) |
| Van Lanschot Kempen | robots.txt disallows automated access to the careers pages |
| Vanguard | in-house careers site with no machine-readable job list found |
| Varenne Capital | in-house careers site with no machine-readable job list found |
| Vattenfall | in-house careers site with no machine-readable job list found |
| Veolia | robots.txt disallows automated access to its job search |
| Vinci | the Ashby board "vinci" belongs to an AI start-up, not to the Vinci group; jobs.vinci.com has no machine-readable job list supported yet. |
| Vitol | robots.txt disallows automated access to its job search |
| Wavestone | in-house careers site with no machine-readable job list found |
| Wells Fargo | in-house careers site with no machine-readable job list found |
| Wolverine Trading | in-house careers site with no machine-readable job list found |
| WTW | robots.txt disallows automated access to the careers pages |
| Zürcher Kantonalbank | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.zkb.ch/de/ueber-uns/) |
| Ørsted | careers site blocks automated requests (HTTP 403) |
<!-- coverage:end -->
