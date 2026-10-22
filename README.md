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
88 of 212 employers are scraped daily.

| Employer | Platform |
|---|---|
| Accenture | workday |
| Akuna Capital | greenhouse |
| AQR | greenhouse |
| Arrowstreet Capital | workday |
| Aviva Investors | workday |
| Bank of America | generic |
| Bank of England | oracle |
| Banque de France | workday |
| Barclays | workday |
| BBVA | workday |
| BearingPoint | teamtailor |
| BlackRock | workday |
| BMO Capital Markets | phenom |
| BNY | oracle |
| Brevan Howard | phenom |
| CFM | greenhouse |
| Citi | workday |
| CME Group | workday |
| Da Vinci | greenhouse |
| Daiwa | teamtailor |
| Deloitte | generic |
| Deutsche Bank | workday |
| DRW | greenhouse |
| DZ Bank | successfactors |
| EDF Trading | workday |
| Euroclear | oracle |
| Euronext | workday |
| ExodusPoint | greenhouse |
| EY | successfactors |
| FCA | workday |
| Fidelity International | workday |
| Five Rings | greenhouse |
| Flow Traders | greenhouse |
| Forvis Mazars | greenhouse |
| Gunvor | workday |
| Hudson River Trading | greenhouse |
| IMC | greenhouse |
| Invesco | workday |
| Jane Street | greenhouse |
| Jefferies | generic |
| JPMorgan | oracle |
| Jump Trading | greenhouse |
| Kepler Cheuvreux | teamtailor |
| Lazard | oracle |
| LBBW | successfactors |
| Lloyds Banking Group | workday |
| Lombard Odier | workday |
| LSEG | workday |
| M&G | workday |
| Macquarie | generic |
| Mako | greenhouse |
| Man Group | greenhouse |
| Marshall Wace | greenhouse |
| Maven Securities | greenhouse |
| Mizuho | workday |
| Morgan Stanley | workday |
| MUFG | workday |
| Murex | workday |
| Nomura | generic |
| Nordea | teamtailor |
| Numerix | greenhouse |
| Optiver | greenhouse |
| PIMCO | workday |
| Point72 | greenhouse |
| PwC | workday |
| Quadrature Capital | greenhouse |
| Qube Research & Technologies | greenhouse |
| Raiffeisen Bank International | successfactors |
| RBC Capital Markets | workday |
| Rothschild & Co | generic |
| S&P Global | workday |
| Santander CIB | workday |
| Schonfeld | greenhouse |
| Schroders | oracle |
| SCOR | oracle |
| Scotiabank | successfactors |
| Shell Trading | workday |
| Squarepoint | greenhouse |
| State Street | workday |
| TD Securities | workday |
| Tower Research | greenhouse |
| Trafigura | workday |
| UniCredit | generic |
| Virtu Financial | greenhouse |
| Vontobel | workday |
| XTX Markets | greenhouse |
| Zanders | teamtailor |
| Zurich | successfactors |

**Not covered yet**, with the reason:

| Employer | Reason |
|---|---|
| ABN AMRO | careers site not reachable by a script (HTTPError: 503 Server Error: Service Unavailable for url: https://www.abnamro.co) |
| ACPR | in-house careers site with no machine-readable job list found |
| Agence France Trésor | in-house careers site with no machine-readable job list found |
| Allianz | uses phenom, successfactors, which has no public job API supported yet |
| Allianz GI | uses phenom, successfactors, which has no public job API supported yet |
| AMF | robots.txt disallows automated access to the careers pages |
| Amundi | in-house careers site with no machine-readable job list found |
| Amundi Luxembourg | in-house careers site with no machine-readable job list found |
| Avantage Reply | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.reply.com/en/careers) |
| AXA | robots.txt disallows automated access to its job search |
| AXA IM | careers site blocks automated requests (HTTP 403) |
| AXA XL | uses cornerstone, which has no public job API supported yet |
| Balyasny | in-house careers site with no machine-readable job list found |
| Banque Cantonale Vaudoise | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.bcv.ch/fr/la-bcv/emp) |
| Banque centrale du Luxembourg | in-house careers site with no machine-readable job list found |
| Banque Internationale à Luxembourg | in-house careers site with no machine-readable job list found |
| Banque mondiale | uses cornerstone, which has no public job API supported yet |
| BCE (ECB) | robots.txt disallows automated access to the careers pages |
| BEI (EIB) | robots.txt disallows automated access to the careers pages |
| Belfius | careers site not reachable by a script (HTTPError: 500 Server Error: Internal Server Error for url: https://www.belfius.) |
| BGL BNP Paribas | in-house careers site with no machine-readable job list found |
| Bloomberg | uses avature, which has no public job API supported yet |
| BlueCrest | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.bluecrestcapital.com) |
| BNP Paribas | candidate platforms failed (HTTPError: 403 Client Error: Forbidden for url: https://group.bnpparibas/en/care) |
| BNP Paribas AM | careers site blocks automated requests (HTTP 403) |
| BNP Paribas Cardif | in-house careers site with no machine-readable job list found |
| BNP Paribas Fortis | careers site not reachable by a script (HTTPError: 503 Server Error: Service Unavailable for url: https://www.bnpparibas) |
| BNS (SNB) | uses successfactors, which has no public job API supported yet |
| BP Trading | careers site blocks automated requests (HTTP 403) |
| Bpifrance | careers site blocks automated requests (HTTP 403) |
| BRI (BIS) | in-house careers site with no machine-readable job list found |
| Bundesbank | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.bundesbank.de/en/bun) |
| Caisse des Dépôts | in-house careers site with no machine-readable job list found |
| Candriam | in-house careers site with no machine-readable job list found |
| Capgemini Invent | robots.txt disallows automated access to the careers pages |
| Capula | careers site not reachable by a script (HTTPError: 429 Client Error: Too Many Requests for url: https://apply.workable.c) |
| Carmignac | in-house careers site with no machine-readable job list found |
| CIC Market Solutions | robots.txt disallows automated access to the careers pages |
| Citadel | careers site blocks automated requests (HTTP 403) |
| Citadel Securities | careers site blocks automated requests (HTTP 403) |
| CNP Assurances | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.cnp.fr/le-groupe-cnp) |
| Comgest | careers site not reachable by a script (HTTPError: 404 Client Error: Page not found for url: https://www.comgest.com/en/) |
| Commerzbank | robots.txt disallows automated access to the careers pages |
| Covéa | robots.txt disallows automated access to its job search |
| Crédit Agricole CIB | uses teamtailor, which has no public job API supported yet |
| Crédit Agricole Indosuez | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://ca-indosuez.com/en/caree) |
| D. E. Shaw | in-house careers site with no machine-readable job list found |
| Danske Bank | robots.txt disallows automated access to the careers pages |
| De Nederlandsche Bank | in-house careers site with no machine-readable job list found |
| Degroof Petercam | in-house careers site with no machine-readable job list found |
| Deutsche Börse / Eurex | the only Workday site found belongs to ISS (a subsidiary), not to Deutsche Börse / Eurex; careers site is in-house. |
| DNCA Finance | in-house careers site with no machine-readable job list found |
| EBA | careers site blocks automated requests (HTTP 403) |
| Edmond de Rothschild | candidate platforms failed (ConnectionError: HTTPSConnectionPool(host='fa-evht-saasfaprod1.fa.ocs.oracleclou) |
| EFG International | careers site blocks automated requests (HTTP 403) |
| Engie GEMS | uses successfactors, which has no public job API supported yet |
| ESMA | careers site blocks automated requests (HTTP 403) |
| Exane (BNP Paribas) | careers site not reachable by a script (ReadTimeout: HTTPSConnectionPool(host='www.exane.com', port=443): Read timed out) |
| FactSet | candidate platforms failed (HTTPError: 422 Client Error: Unprocessable Entity for url: https://factset.wd1.m) |
| FEI (EIF) | in-house careers site with no machine-readable job list found |
| Finalyse | in-house careers site with no machine-readable job list found |
| Finastra | candidate platforms failed (HTTPError: 404 Client Error: Not Found for url: https://finastra.wd3.myworkdayjo) |
| Fitch Ratings | candidate platforms failed (HTTPError: 422 Client Error: Unprocessable Entity for url: https://fitch.wd1.myw) |
| FMI (IMF) | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.imf.org/en/Careers) |
| G-Research | robots.txt disallows automated access to the careers pages |
| Generali | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.generali.com/careers) |
| Generali Investments | in-house careers site with no machine-readable job list found |
| Glencore | in-house careers site with no machine-readable job list found |
| Goldman Sachs | uses avature, which has no public job API supported yet |
| Groupama AM | in-house careers site with no machine-readable job list found |
| HSBC | robots.txt disallows automated access to the careers pages |
| HSBC Continental Europe | robots.txt disallows automated access to the careers pages |
| ICE | candidate platforms failed (HTTPError: 422 Client Error: Unprocessable Entity for url: https://intercontinen) |
| ING | robots.txt disallows automated access to its job search |
| Intesa Sanpaolo | in-house careers site with no machine-readable job list found |
| Investec | candidate platforms failed (HTTPError: 422 Client Error: Unprocessable Entity for url: https://investec.wd3.) |
| ION Group | in-house careers site with no machine-readable job list found |
| Janus Henderson | candidate platforms failed (HTTPError: 422 Client Error: Unprocessable Entity for url: https://janushenderso) |
| Julius Baer | careers site blocks automated requests (HTTP 403) |
| KBC | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.kbc.com/en/careers.h) |
| KPMG | uses radancy, which has no public job API supported yet |
| La Banque Postale | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.labanquepostale.com/) |
| La Française | in-house careers site with no machine-readable job list found |
| Legal & General | careers site not reachable by a script (ConnectionError: HTTPSConnectionPool(host='www.legalandgeneralgroup.com', port=4) |
| Leonteq | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.leonteq.com/company/) |
| Marex | careers site not reachable by a script (ConnectionError: HTTPConnectionPool(host='www.marex.test', port=80): Max retries) |
| Mediobanca | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.mediobanca.com/en/ca) |
| Mercuria | careers site not reachable by a script (SSLError: HTTPSConnectionPool(host='mercuria.com', port=443): Max retries exceed) |
| MES (ESM) | robots.txt disallows automated access to the careers pages |
| Millennium | robots.txt disallows automated access to its job search |
| Mirova | in-house careers site with no machine-readable job list found |
| Moody's | robots.txt disallows automated access to its job search |
| MSCI | candidate platforms failed (HTTPError: 401 Client Error: Unauthorized for url: https://msci.wd1.myworkdayjob) |
| Munich Re | robots.txt disallows automated access to its job search |
| Natixis CIB | in-house careers site with no machine-readable job list found |
| Natixis IM | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.im.natixis.com/en-in) |
| NatWest Markets | careers site blocks automated requests (HTTP 403) |
| Oddo BHF | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.oddo-bhf.com/fr/rejo) |
| Ofi Invest | in-house careers site with no machine-readable job list found |
| Ostrum | in-house careers site with no machine-readable job list found |
| Pictet | uses successfactors, which has no public job API supported yet |
| Rabobank | careers site blocks automated requests (HTTP 403) |
| Robeco | in-house careers site with no machine-readable job list found |
| SEB | in-house careers site with no machine-readable job list found |
| Sia Partners | robots.txt disallows automated access to its job search |
| SimCorp | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.simcorp.com/careers) |
| SMBC | uses successfactors, which has no public job API supported yet |
| Société Générale | uses taleo, which has no public job API supported yet |
| Société Générale Luxembourg | in-house careers site with no machine-readable job list found |
| Spuerkeess (BCEE) | uses cornerstone, which has no public job API supported yet |
| Standard Chartered | uses successfactors, which has no public job API supported yet |
| Susquehanna (SIG) | robots.txt disallows automated access to its job search |
| Swiss Life AM | careers site blocks automated requests (HTTP 403) |
| Swiss Re | candidate platforms failed (HTTPError: 404 Client Error: Not Found for url: https://www.swissre.com/search/?) |
| Swissquote | robots.txt disallows automated access to its job search |
| Sycomore AM | robots.txt disallows automated access to its job search |
| Tikehau Capital | in-house careers site with no machine-readable job list found |
| TotalEnergies Trading | robots.txt disallows automated access to the careers pages |
| Two Sigma | in-house careers site with no machine-readable job list found |
| UBS | candidate platforms failed (HTTPError: 404 Client Error: Not Found for url: https://www.ubs.com/search-jobs/) |
| Vitol | robots.txt disallows automated access to its job search |
| Wavestone | in-house careers site with no machine-readable job list found |
| Wells Fargo | in-house careers site with no machine-readable job list found |
| Zürcher Kantonalbank | careers site not reachable by a script (HTTPError: 404 Client Error: Not Found for url: https://www.zkb.ch/de/ueber-uns/) |
<!-- coverage:end -->
