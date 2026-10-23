"""Find which recruitment platform an employer uses, and test it.

For each employer in tools/employers.yaml:
  1. fetches its careers page (falling back to the site root) and a few
     job-related links, looking for platform signatures (myworkdayjobs.com,
     greenhouse.io, oraclecloud.com, tal.net, ...);
  2. probes the public APIs of Greenhouse, Lever, SmartRecruiters, Ashby,
     Workable, Recruitee and Teamtailor with slugs derived from its name;
  3. turns every finding into a candidate target configuration and runs the
     real adapter on it with the search term "intern", so each candidate comes
     with a verdict: works / blocked by robots.txt / error, plus sample titles.

Writes discovery/results.json and discovery/results.md, used to fill
targets.yaml. It never runs in the daily job.

    python tools/discover.py                    # all employers
    python tools/discover.py --only "Jane Street"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import yaml
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tracker import filters, gha  # noqa: E402
from tracker.adapters import get_adapter  # noqa: E402
from tracker.http import PoliteClient, RobotsDisallowed  # noqa: E402
from tracker.models import Target, slugify  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "discovery"

SIGNATURES = {
    "workday": re.compile(r"https?://([\w-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([\w-]+)"),
    "oracle": re.compile(r"https?://([\w.-]+\.oraclecloud\.com)/hcmUI/CandidateExperience/[\w-]+/sites/([\w-]+)"),
    "greenhouse": re.compile(r"(?:boards|job-boards)(?:\.eu)?\.greenhouse\.io/(?:embed/job_board(?:/js)?\?for=)?([\w-]+)"),
    "lever": re.compile(r"jobs\.(?:eu\.)?lever\.co/([\w-]+)"),
    "smartrecruiters": re.compile(r"(?:jobs|careers)\.smartrecruiters\.com/([\w-]+)"),
    "ashby": re.compile(r"jobs\.ashbyhq\.com/([\w-]+)"),
    "workable": re.compile(r"apply\.workable\.com/([\w-]+)"),
    "recruitee": re.compile(r"([\w-]+)\.recruitee\.com"),
    "teamtailor": re.compile(r"([\w-]+)\.teamtailor\.com"),
    "eightfold": re.compile(r"([\w-]+\.eightfold\.ai)"),
    "phenom": re.compile(r"(phApp\.ddo|cdn\.phenompeople\.com)"),
    "radancy": re.compile(r"(tbcdn\.talentbrew\.com)"),
    "successfactors": re.compile(r"(rmkcdn\.successfactors\.com|career\d*\.successfactors\.(?:com|eu))"),
    "taleo": re.compile(r"([\w-]+\.taleo\.net)"),
    "icims": re.compile(r"(careers-[\w-]+\.icims\.com|[\w-]+\.icims\.com/jobs)"),
    "oleeo": re.compile(r"([\w-]+\.tal\.net)"),
    "avature": re.compile(r"([\w.-]+\.avature\.net)"),
    "cornerstone": re.compile(r"([\w-]+\.csod\.com)"),
    "welcometothejungle": re.compile(r"welcometothejungle\.com/(?:fr|en)/companies/([\w-]+)"),
    "jsonld": re.compile(r'"@type"\s*:\s*"JobPosting"'),
}

# Links worth keeping as candidate entry points for HTML-based platforms.
ENTRY_LINKS = re.compile(r"SearchJobs|tal\.net/|icims\.com/jobs|/search/\?q=|search-results|/search-jobs|jobboard", re.I)
JOB_LINK_HINT = re.compile(r"job|career|carri|search|offre|emploi|vacanc|opportunit|stage|intern|join|recrut|karriere|stellen", re.I)


def slug_candidates(name: str, extra: list[str]) -> list[str]:
    base = slugify(name)
    return [c for c in dict.fromkeys(extra + [base.replace("-", ""), base]) if len(c) >= 3]


def scan(text: str) -> dict:
    hits = {}
    for platform, rx in SIGNATURES.items():
        found = sorted({"|".join(g or "" for g in m.groups()) if m.groups() else m.group(0) for m in rx.finditer(text)})
        if found:
            hits[platform] = found[:5]
    return hits


def probe_page(http, url: str, depth: int, pages: list) -> None:
    entry = {"url": url, "final_url": "", "signatures": {}, "entry_links": [], "error": ""}
    pages.append(entry)
    try:
        resp = http.get(url, retries=0, allow_redirects=True)
    except Exception as exc:
        entry["error"] = f"{type(exc).__name__}: {exc}"[:200]
        return
    entry["final_url"] = resp.url
    html = resp.text
    entry["signatures"] = scan(html)
    soup = BeautifulSoup(html, "html.parser")
    hrefs = [urljoin(resp.url, a["href"]) for a in soup.find_all("a", href=True)]
    entry["entry_links"] = sorted({h for h in hrefs if ENTRY_LINKS.search(h)})[:10]
    if depth <= 0:
        return
    host = urlsplit(resp.url).netloc
    links = []
    for a in soup.find_all("a", href=True):
        href = urljoin(resp.url, a["href"]).split("#")[0]
        if href.startswith("http") and href != resp.url and href not in links and (
                JOB_LINK_HINT.search(href) or JOB_LINK_HINT.search(a.get_text(" ", strip=True))):
            links.append(href)
    links.sort(key=lambda h: urlsplit(h).netloc == host)  # external (ATS) links first
    for href in links[:6]:
        probe_page(http, href, depth - 1, pages)


def probe_apis(http, slugs: list[str]) -> list[tuple[str, dict]]:
    checks = {
        "greenhouse": ("https://boards-api.greenhouse.io/v1/boards/{s}/jobs", lambda d: len(d.get("jobs", [])), "board"),
        "lever": ("https://api.lever.co/v0/postings/{s}?mode=json", lambda d: len(d) if isinstance(d, list) else 0, "site"),
        "smartrecruiters": ("https://api.smartrecruiters.com/v1/companies/{s}/postings?limit=1", lambda d: d.get("totalFound", 0), "company"),
        "ashby": ("https://api.ashbyhq.com/posting-api/job-board/{s}", lambda d: len(d.get("jobs", [])), "board"),
        "workable": ("https://apply.workable.com/api/v1/widget/accounts/{s}", lambda d: len(d.get("jobs", [])), "account"),
        "recruitee": ("https://{s}.recruitee.com/api/offers/", lambda d: len(d.get("offers", [])), "company"),
    }
    found = []
    for platform, (template, count, key) in checks.items():
        for slug in slugs:
            try:
                if count(http.get_json(template.format(s=slug), retries=0)):
                    found.append((platform, {key: slug}))
                    break
            except Exception:
                continue
    for slug in slugs:
        try:
            if "<rss" in http.get(f"https://{slug}.teamtailor.com/jobs.rss", retries=0).text:
                found.append(("teamtailor", {"base": f"https://{slug}.teamtailor.com"}))
                break
        except Exception:
            continue
    return found


def site_root(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


def phenom_base(url: str) -> str:
    parts = urlsplit(url)
    segs = [s for s in parts.path.split("/") if s]
    keep = []
    for seg in segs[:2]:
        if re.fullmatch(r"[a-z]{2}(-[a-z]{2})?", seg):
            keep.append(seg)
    return site_root(url) + ("/" + "/".join(keep) if keep else "")


def registrable_domain(url: str) -> str:
    host = urlsplit(url).netloc.split(":")[0]
    parts = host.split(".")
    return ".".join(parts[-3:]) if parts[-2] in ("co", "com") and len(parts) > 2 else ".".join(parts[-2:])


def candidates_for(employer: dict, pages: list, apis: list) -> list[tuple[str, dict]]:
    cands: list[tuple[str, dict]] = list(apis)
    for page in pages:
        sigs, final = page["signatures"], page["final_url"] or page["url"]
        for entry in sigs.get("workday", [])[:3]:
            tenant, wd, site = entry.split("|")
            if site.lower() not in ("en-us", "fr-fr", "en-gb", "wday"):
                cands.append(("workday", {"url": f"https://{tenant}.{wd}.myworkdayjobs.com/{site}"}))
        for entry in sigs.get("oracle", [])[:3]:
            host, site = entry.split("|")
            cands.append(("oracle", {"host": host, "site": site}))
        for slug in sigs.get("greenhouse", [])[:2]:
            if slug not in ("embed", "v1"):
                cands.append(("greenhouse", {"board": slug}))
        for slug in sigs.get("lever", [])[:2]:
            cands.append(("lever", {"site": slug}))
        for slug in sigs.get("smartrecruiters", [])[:2]:
            cands.append(("smartrecruiters", {"company": slug}))
        for host in sigs.get("eightfold", [])[:1]:
            if host not in ("app.eightfold.ai",):
                cands.append(("eightfold", {"host": host, "domain": registrable_domain(employer["careers_url"])}))
        if "phenom" in sigs:
            cands.append(("phenom", {"base": phenom_base(final)}))
        if "radancy" in sigs:
            cands.append(("radancy", {"base": site_root(final)}))
        if "successfactors" in sigs and not urlsplit(final).netloc.startswith("career"):
            cands.append(("successfactors", {"base": site_root(final)}))
        for link in page["entry_links"]:
            if "/search/?q=" in link:
                cands.append(("successfactors", {"base": site_root(link)}))
            elif "SearchJobs" in link:
                base = link.split("SearchJobs")[0].rstrip("/")
                cands.append(("generic", {"urls": [base + "/SearchJobs/?search={term}"], "link_pattern": "JobDetail"}))
            elif "icims.com/jobs" in link:
                cands.append(("generic", {"urls": [site_root(link) + "/jobs/search?ss=1&searchKeyword={term}&in_iframe=1"],
                                          "link_pattern": r"/jobs/\d+/"}))
            elif "tal.net/" in link:
                cands.append(("generic", {"urls": [link], "link_pattern": r"/opp/\d+"}))
            elif "/search-jobs" in link:
                cands.append(("radancy", {"base": site_root(link)}))
        if "jsonld" in sigs:
            cands.append(("generic", {"urls": [final]}))
    for platform, params in employer.get("candidates", []) or []:
        cands.append((platform, params))
    # De-duplicate while keeping order.
    seen, unique = set(), []
    for platform, params in cands:
        key = (platform, json.dumps(params, sort_keys=True))
        if key not in seen:
            seen.add(key)
            unique.append((platform, params))
    return unique[:8]


def test_candidate(http, name: str, platform: str, params: dict) -> dict:
    target = Target(name=name, type="test", platform=platform, careers_url="",
                    params={**params, "search_terms": ["intern"]})
    try:
        raw = get_adapter(platform).fetch(target, http)
    except RobotsDisallowed as exc:
        return {"platform": platform, "params": params, "status": "robots", "error": str(exc)[:200]}
    except Exception as exc:
        return {"platform": platform, "params": params, "status": "error", "error": f"{type(exc).__name__}: {exc}"[:200]}
    interns = [r for r in raw if filters.keep(r.title, r.employment_type)]
    return {"platform": platform, "params": params, "status": "ok", "fetched": len(raw),
            "internships": len(interns), "sample": [f"{r.title} | {r.location}" for r in interns[:6]]
            or [f"{r.title} | {r.location}" for r in raw[:3]]}


def discover(http, employer: dict) -> dict:
    pages: list = []
    for url in [employer.get("careers_url")] + employer.get("extra_urls", []):
        if url:
            probe_page(http, url, 1, pages)
    if all(p["error"] or not p["signatures"] for p in pages) and employer.get("careers_url"):
        root = site_root(employer["careers_url"])
        if root.rstrip("/") != employer["careers_url"].rstrip("/"):
            probe_page(http, root + "/", 1, pages)
    apis = probe_apis(http, slug_candidates(employer["name"], employer.get("slugs", [])))
    tests = [test_candidate(http, employer["name"], p, params) for p, params in candidates_for(employer, pages, apis)]
    signatures = {}
    for p in pages:
        for k, v in p["signatures"].items():
            signatures[k] = sorted(set(signatures.get(k, [])) | set(v))[:5]
    best = max((t for t in tests if t["status"] == "ok"), key=lambda t: (t["internships"], t["fetched"]), default=None)
    return {"name": employer["name"], "type": employer.get("type", ""), "careers_url": employer.get("careers_url", ""),
            "signatures": signatures, "page_errors": [p["error"] for p in pages if p["error"]][:3],
            "tests": tests, "best": best}


def to_markdown(results: list[dict]) -> str:
    lines = ["# Platform discovery", "",
             "| Employer | Best candidate | Internships found | Other findings |", "|---|---|---|---|"]
    for r in results:
        best = r["best"]
        best_txt = f"**{best['platform']}** `{json.dumps(best['params'])}`" if best else "—"
        n = f"{best['internships']} / {best['fetched']}" if best else "—"
        other = "; ".join(f"{t['platform']}: {t['status']}" for t in r["tests"] if t is not best)
        other += (" · signatures: " + ", ".join(r["signatures"])) if r["signatures"] else ""
        other += (" · page errors: " + "; ".join(e[:60] for e in r["page_errors"])) if r["page_errors"] else ""
        lines.append(f"| {r['name']} | {best_txt} | {n} | {other or '—'} |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", action="append")
    parser.add_argument("--input", default=str(ROOT / "tools" / "employers.yaml"))
    args = parser.parse_args(argv)
    employers = yaml.safe_load(Path(args.input).read_text(encoding="utf-8"))["employers"]
    if args.only:
        wanted = {n.strip().lower() for names in args.only for n in names.split(",")}
        employers = [e for e in employers if e["name"].lower() in wanted]
    http = PoliteClient(min_delay=1.0, timeout=20)

    def run(employer):
        print(f"... {employer['name']}", flush=True)
        try:
            return discover(http, employer)
        except Exception as exc:
            return {"name": employer["name"], "type": employer.get("type", ""), "careers_url": employer.get("careers_url", ""),
                    "signatures": {}, "page_errors": [str(exc)[:200]], "tests": [], "best": None}

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(run, employers))
    OUT.mkdir(exist_ok=True)
    if args.only and (OUT / "results.json").exists():
        # Partial run: update those employers in the previous results.
        previous = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
        fresh = {r["name"]: r for r in results}
        results = [fresh.pop(r["name"], r) for r in previous] + list(fresh.values())
    (OUT / "results.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT / "results.md").write_text(to_markdown(results), encoding="utf-8")
    found = sum(1 for r in results if r["best"])
    gha.notice("Discovery", [f"{found}/{len(results)} employers with a working candidate"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
