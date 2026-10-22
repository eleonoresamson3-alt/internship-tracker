"""Find which recruitment platform an employer uses.

For each employer in tools/employers.yaml:
  1. fetches its careers page (and a few job-related links on it) and looks
     for known platform signatures (myworkdayjobs.com, greenhouse.io, ...);
  2. probes the public APIs of Greenhouse, Lever, SmartRecruiters, Ashby,
     Workable, Recruitee and Teamtailor with slugs derived from its name;
  3. for every Workday / Oracle site found, runs an "intern" search to check
     that the endpoint works and how many offers it returns.

Writes discovery/results.json and discovery/results.md. Used to fill
targets.yaml; it never runs in the daily job.

    python tools/discover.py                    # all employers
    python tools/discover.py --only "Jane Street"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import yaml
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tracker.http import PoliteClient  # noqa: E402
from tracker.models import slugify  # noqa: E402

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
    "successfactors": re.compile(r"(career\d*\.successfactors\.(?:com|eu)[^\"'\s<>]*|[\w.-]+/search/\?q=|rmkcdn\.successfactors\.com)"),
    "eightfold": re.compile(r"([\w-]+\.eightfold\.ai|/api/apply/v2/jobs)"),
    "phenom": re.compile(r"(phApp\.ddo|cdn\.phenompeople\.com)"),
    "radancy": re.compile(r"(tbcdn\.talentbrew\.com|/search-jobs)"),
    "avature": re.compile(r"([\w.-]+\.avature\.net|/SearchJobs)"),
    "taleo": re.compile(r"([\w-]+\.taleo\.net)"),
    "icims": re.compile(r"([\w-]+\.icims\.com)"),
    "oleeo": re.compile(r"([\w-]+\.tal\.net)"),
    "jobvite": re.compile(r"jobs\.jobvite\.com/([\w-]+)"),
    "welcometothejungle": re.compile(r"welcometothejungle\.com/(?:fr|en)/companies/([\w-]+)"),
    "cornerstone": re.compile(r"([\w-]+\.csod\.com)"),
    "beesite": re.compile(r"(beesite|milchundzucker)"),
    "jsonld_jobposting": re.compile(r'"@type"\s*:\s*"JobPosting"'),
}

JOB_LINK_HINT = re.compile(r"job|career|carri|search|offre|emploi|vacanc|opportunit|stage|intern|join|recrut|karriere|stellen", re.I)


def slug_candidates(name: str, extra: list[str]) -> list[str]:
    base = slugify(name)
    compact = base.replace("-", "")
    cands = list(dict.fromkeys(extra + [compact, base]))
    return [c for c in cands if len(c) >= 3]


def scan(text: str) -> dict:
    hits = {}
    for platform, rx in SIGNATURES.items():
        found = sorted({m.group(0) if not m.groups() else "|".join(g or "" for g in m.groups())
                        for m in rx.finditer(text)})
        if found:
            hits[platform] = found[:5]
    return hits


def probe_page(http, url: str, depth: int = 1) -> dict:
    report = {"url": url, "signatures": {}, "followed": [], "error": ""}
    try:
        resp = http.get(url, retries=0, allow_redirects=True)
        report["final_url"] = resp.url
        html = resp.text
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"[:300]
        return report
    report["signatures"] = scan(html)
    if depth > 0:
        soup = BeautifulSoup(html, "html.parser")
        host = urlsplit(resp.url).netloc
        links = []
        for a in soup.find_all("a", href=True):
            href = urljoin(resp.url, a["href"])
            text = a.get_text(" ", strip=True)
            if href.startswith("http") and (JOB_LINK_HINT.search(href) or JOB_LINK_HINT.search(text)):
                if href not in links and href.split("#")[0] != resp.url:
                    links.append(href)
        # Prefer external links (ATS) and then same-host job pages.
        links.sort(key=lambda h: urlsplit(h).netloc == host)
        for href in links[:6]:
            sub = probe_page(http, href, depth - 1)
            report["followed"].append({"url": href, "signatures": sub["signatures"], "error": sub["error"]})
    return report


def probe_apis(http, slugs: list[str]) -> dict:
    found = {}
    checks = {
        "greenhouse": ("https://boards-api.greenhouse.io/v1/boards/{s}/jobs", lambda d: len(d.get("jobs", []))),
        "lever": ("https://api.lever.co/v0/postings/{s}?mode=json", lambda d: len(d) if isinstance(d, list) else 0),
        "lever_eu": ("https://api.eu.lever.co/v0/postings/{s}?mode=json", lambda d: len(d) if isinstance(d, list) else 0),
        "smartrecruiters": ("https://api.smartrecruiters.com/v1/companies/{s}/postings?limit=1", lambda d: d.get("totalFound", 0)),
        "ashby": ("https://api.ashbyhq.com/posting-api/job-board/{s}", lambda d: len(d.get("jobs", []))),
        "workable": ("https://apply.workable.com/api/v1/widget/accounts/{s}", lambda d: len(d.get("jobs", []))),
        "recruitee": ("https://{s}.recruitee.com/api/offers/", lambda d: len(d.get("offers", []))),
    }
    for platform, (template, count) in checks.items():
        for slug in slugs:
            url = template.format(s=slug)
            try:
                n = count(http.get_json(url, retries=0))
            except Exception:
                continue
            if n:
                found[platform] = {"slug": slug, "offers": n}
                break
    for slug in slugs:
        try:
            xml = http.get(f"https://{slug}.teamtailor.com/jobs.rss", retries=0).text
            if "<rss" in xml:
                found["teamtailor"] = {"slug": slug, "offers": xml.count("<item>")}
                break
        except Exception:
            continue
    return found


def check_workday(http, host: str, tenant: str, site: str) -> dict:
    try:
        data = http.post_json(f"https://{host}/wday/cxs/{tenant}/{site}/jobs",
                              {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "intern"}, retries=0)
        return {"ok": True, "intern_total": data.get("total"),
                "sample": [j.get("title") for j in data.get("jobPostings", [])[:5]]}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"[:200]}


def check_oracle(http, host: str, site: str) -> dict:
    url = (f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true"
           f"&finder=findReqs;siteNumber={site},limit=5,offset=0,keyword=%22intern%22")
    try:
        data = http.get_json(url, retries=0)
        block = (data.get("items") or [{}])[0]
        return {"ok": True, "intern_total": block.get("TotalJobsCount"),
                "sample": [r.get("Title") for r in block.get("requisitionList", [])[:5]]}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"[:200]}


def all_signatures(page_report: dict) -> dict:
    merged = {}
    for sigs in [page_report.get("signatures", {})] + [f["signatures"] for f in page_report.get("followed", [])]:
        for k, v in sigs.items():
            merged.setdefault(k, [])
            merged[k] = sorted(set(merged[k]) | set(v))[:8]
    return merged


def discover(http, employer: dict) -> dict:
    result = {"name": employer["name"], "careers_url": employer.get("careers_url", "")}
    pages = []
    for url in [employer.get("careers_url")] + employer.get("extra_urls", []):
        if url:
            pages.append(probe_page(http, url))
    result["pages"] = pages
    sigs = {}
    for p in pages:
        for k, v in all_signatures(p).items():
            sigs[k] = sorted(set(sigs.get(k, [])) | set(v))
    result["signatures"] = sigs
    result["apis"] = probe_apis(http, slug_candidates(employer["name"], employer.get("slugs", [])))
    checks = {}
    for entry in sigs.get("workday", [])[:3]:
        tenant, wd, site = entry.split("|")
        host = f"{tenant}.{wd}.myworkdayjobs.com"
        checks[f"workday:{host}/{site}"] = check_workday(http, host, tenant, site)
    for entry in employer.get("workday", []):
        parts = urlsplit(entry)
        host = parts.netloc
        site = [s for s in parts.path.split("/") if s and not re.match(r"^[a-z]{2}-[A-Z]{2}$", s)][0]
        checks[f"workday:{host}/{site}"] = check_workday(http, host, host.split(".")[0], site)
    for entry in sigs.get("oracle", [])[:2] + employer.get("oracle", []):
        host, site = entry.split("|")
        checks[f"oracle:{host}/{site}"] = check_oracle(http, host, site)
    result["checks"] = checks
    return result


def to_markdown(results: list[dict]) -> str:
    lines = ["# Platform discovery", "", "| Employer | Careers page | Signatures | Public APIs | Endpoint checks |",
             "|---|---|---|---|---|"]
    for r in results:
        page_errors = "; ".join(p["error"] for p in r["pages"] if p.get("error"))
        sigs = "<br>".join(f"**{k}**: {', '.join(v[:3])}" for k, v in r["signatures"].items()) or "—"
        apis = "<br>".join(f"**{k}**: {v['slug']} ({v['offers']})" for k, v in r["apis"].items()) or "—"
        checks = "<br>".join(
            f"{k}: " + (f"OK, {v.get('intern_total')} intern hits" if v.get("ok") else f"FAIL {v.get('error', '')}")
            for k, v in r["checks"].items()) or "—"
        page = r["careers_url"] + (f" (error: {page_errors})" if page_errors else "")
        lines.append(f"| {r['name']} | {page} | {sigs} | {apis} | {checks} |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", action="append")
    parser.add_argument("--input", default=str(ROOT / "tools" / "employers.yaml"))
    args = parser.parse_args(argv)
    employers = yaml.safe_load(Path(args.input).read_text(encoding="utf-8"))["employers"]
    if args.only:
        wanted = {n.lower() for n in args.only}
        employers = [e for e in employers if e["name"].lower() in wanted]
    http = PoliteClient(min_delay=1.0, timeout=20)
    results = []
    for employer in employers:
        print(f"... {employer['name']}", flush=True)
        try:
            results.append(discover(http, employer))
        except Exception as exc:
            results.append({"name": employer["name"], "careers_url": employer.get("careers_url", ""),
                            "pages": [{"error": str(exc)}], "signatures": {}, "apis": {}, "checks": {}})
    OUT.mkdir(exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT / "results.md").write_text(to_markdown(results), encoding="utf-8")
    print(f"wrote {OUT / 'results.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
