# Security

This repository scrapes public job offers and RSS feeds every day and publishes them on a static
GitHub Pages site. Personal tracking (application statuses, notes, trainings) lives **only in the
visitor's browser** (`localStorage`). It is never sent to a server and never committed.

## Reporting a problem

Please do not open a public issue for a vulnerability. Use **Security → Report a vulnerability**
(GitHub private vulnerability reporting) on this repository. If that is not available, contact the
repository owner through their GitHub profile. You should get an answer within a week.

## Protections in place

### External content (job offers, RSS, generated analyses)

| Layer | Protection |
|---|---|
| Collection (Python) | [`tracker/sanitize.py`](tracker/sanitize.py): every scraped title, location, RSS title and summary is turned into plain text. HTML entities are decoded, tags and `<script>`/`<style>`/`<iframe>`/`<svg>` blocks are removed, control and bidi-override characters are stripped, and length is capped. URLs are kept only if they are absolute `http(s)` with a host. `javascript:`, `data:`, `vbscript:`, `file:`, protocol-relative and credential-bearing URLs are rejected. An offer or article without a safe link is dropped. |
| Generated analyses | `tracker/news/analyses.py` rejects any source URL that is not a safe `https://` link before the file is published. The scheduled session's instructions ([`ANALYSES.md`](ANALYSES.md)) treat article text as data, never as instructions (prompt-injection guard). |
| E-mail digest | `tracker/notify.py` escapes scraped text as inert Markdown: no links, images, HTML or `@mentions` from scraped data. Only safe URLs become links. |
| Site (JavaScript) | Nothing is ever built from HTML strings: no `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write` or `eval`. All text goes through `textContent`. Every link goes through `setLink()`, which accepts only `http(s)` URLs and adds `target="_blank" rel="noopener noreferrer"`. A rejected URL leaves plain text. |
| CSV export | Cells starting with `=`, `+`, `-`, `@` are prefixed with `'`, so a scraped title cannot become a spreadsheet formula (CSV injection). The prefix is removed again on import. |
| Tests | [`tests/test_security.py`](tests/test_security.py): malicious payloads (`<script>`, `onerror`, `javascript:` links, escaped markup, bidi characters) through the Python cleaning, the RSS parser and the digest. A static check that the site's JavaScript has no HTML sinks and sets links only through `setLink()`. A browser test (run when Playwright is installed) loads hostile data into every tab and checks that nothing executes and that no `javascript:` link exists. |

### Browser

- **Content-Security-Policy** (meta tag in `docs/index.html`): `default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; manifest-src 'self'; base-uri 'none'; form-action 'none'; object-src 'none'; upgrade-insecure-requests`.
  - No inline script, no inline event handlers, no third-party script, font or CDN.
  - All code is served from the repository.
- **Referrer-Policy:** `no-referrer`, as a meta tag and on every external link.
- **Known limits of GitHub Pages:** it does not allow custom HTTP headers, so `frame-ancestors` (anti-clickjacking) and HSTS cannot be set by the site.
  - Clickjacking has little impact here: the site only reads data, and actions affect only the visitor's own browser.
  - HTTPS is enforced by the Pages setting (see below).

### GitHub Actions

- **Permissions:** every workflow defaults to `contents: read`, and each job requests only what it needs:
  - commit the data: `contents: write`;
  - daily digest: `issues: write`;
  - Pages deployment: `pages: write` and `id-token: write`;
  - starting the site-only deploy: `actions: write`;
  - CodeQL: `security-events: write`.
- **Pinned actions:** every action is pinned to a full commit SHA, with the version in a comment. Dependabot keeps the pins up to date.
- **Triggers:** no `pull_request_target`. Workflows that write run only on `schedule`, `workflow_dispatch` or pushes to branches that only collaborators can write. CodeQL and the dependency audit run on `pull_request` with a read-only token and `persist-credentials: false`.
- **Secrets:** API keys (`WEBSTAT_API_KEY`, optional `ANTHROPIC_API_KEY`) are repository secrets, passed as environment variables to the single step that needs them. GitHub masks them in logs. They never appear in files or command lines.
- **Logs:** steps that print scraped text run with workflow commands paused (`tools/ci/run-paused.sh`, `::stop-commands::`). A job title or server error starting with `::` cannot inject a workflow command. Run summaries are escaped and printed afterwards (`tracker/gha.py`). User input (`inputs.only`) reaches shell commands only through environment variables, never through `${{ }}` interpolation in `run:`.

### Dependencies

- **Pinned and hashed:** `requirements.txt` pins every package, including transitive ones, with SHA-256 hashes, generated from `requirements.in` with `uv pip compile --generate-hashes`. CI installs with `pip install --require-hashes`.
- **14-day delay:** versions published less than 14 days before resolution are excluded, to avoid a freshly compromised release. The exceptions are listed in `requirements.in`: a security fix, or a feature the code needs.
- **Remote XML:** parsed with `defusedxml`.
- **pip-audit** runs weekly and on every change to the requirements (`.github/workflows/security.yml`).
- **CodeQL** (Python, JavaScript, Actions, `security-extended` queries) runs weekly and on every push or pull request to `main`.
- **Dependabot** (`.github/dependabot.yml`) opens security updates immediately, and version updates for pip and GitHub Actions weekly with a 14-day cooldown.

### Personal data

- **What is stored where:** statuses, notes, trainings and contacts are stored in `localStorage` only. CSV and JSON exports are downloaded to the visitor's computer, and `.gitignore` excludes them, as well as `.env` files, keys and logs.
- **Nothing personal in the repository:** the committed data (`data/*.json`) contains public job offers, public news headlines and public market data only.
- **Personal e-mail in commit history:** commits made through the GitHub web interface record the author's e-mail in the git history. To avoid exposing a personal address, see *Keep my email addresses private* below.

## Repository settings (done by hand by the owner)

These cannot be set from a file. They are listed in the audit report and kept here for reference:

1. **Settings → Code security:**
   - enable *Private vulnerability reporting*;
   - enable *Dependency graph*, *Dependabot alerts* and *Dependabot security updates*;
   - enable *Secret scanning* and *Push protection*;
   - leave *CodeQL* on *Advanced* (the workflow in this repository). Do not also enable *Default setup*.
2. **Settings → Rules → Rulesets → New branch ruleset**, target `main`, enforcement *Active*:
   - *Restrict deletions* and *Block force pushes*;
   - *Require a pull request before merging* only if *GitHub Actions* can be added to the bypass
     list. The daily workflow and the analyses workflow commit to `main` with the workflow
     token, and they would otherwise be blocked.
3. **Settings → Pages:** source *GitHub Actions*, and **Enforce HTTPS** checked.
4. **Settings → Actions → General:**
   - *Allow actions*: "Allow owner, and select non-owner, actions", with `actions/*` and `github/codeql-action/*` allowed;
   - *Require approval for all outside collaborators* for fork pull requests;
   - *Workflow permissions*: "Read repository contents" (each workflow requests more where needed);
   - *Allow GitHub Actions to create and approve pull requests* unchecked.
5. **Settings → Environments → github-pages:** deployment branches limited to `main`.
6. **Personal settings → Emails:**
   - check *Keep my email addresses private* and *Block command line pushes that expose my email*;
   - commits made in the GitHub interface will then use the `@users.noreply.github.com` address.
