"""Malicious inputs from scraped pages and RSS feeds must stay inert.

Python side: cleaned at collection time (tracker/sanitize.py). Site side: a
static check that the JavaScript never builds HTML from strings, and a browser
test (skipped when Playwright is not installed) that loads hostile data files
and checks that nothing runs.
"""

import json
import re
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from tracker import notify
from tracker.models import RawJob, Target
from tracker.news import analyses, feeds
from tracker.run import to_record
from tracker.sanitize import clean_text, safe_url

ROOT = Path(__file__).resolve().parents[1]

XSS_TEXT = [
    '<script>window.__pwned=1</script>Quant',
    '<img src=x onerror="window.__pwned=1">Quant',
    '&lt;script&gt;window.__pwned=1&lt;/script&gt;Quant',
    '<svg onload=window.__pwned=1>Quant</svg>',
    'Quant<iframe src="javascript:window.__pwned=1"></iframe>',
    '<a href="javascript:window.__pwned=1">Quant</a>',
    'Quant‮<b',
]
BAD_URLS = [
    "javascript:alert(1)", " JavaScript:alert(1)", "java\tscript:alert(1)", "data:text/html,<script>alert(1)</script>",
    "vbscript:msgbox(1)", "file:///etc/passwd", "//evil.example/x", "/relative/path", "https://user:pw@evil.example/",
    'https://ok.example/"><script>', "https://ok.example/a b", "https://" + "a" * 3000 + ".com",
]


@pytest.mark.parametrize("payload", XSS_TEXT)
def test_clean_text_removes_markup(payload):
    out = clean_text(payload)
    assert "<" not in out and ">" not in out
    assert "script" not in out.lower() and "onerror" not in out.lower() and "onload" not in out.lower()
    assert "‮" not in out


def test_clean_text_keeps_plain_text_and_caps_length():
    assert clean_text("Stage &amp; Structuring  –  Juin 2027") == "Stage & Structuring – Juin 2027"
    assert clean_text("taux < 2 % et spread > 100 pb") == "taux < 2 % et spread > 100 pb"
    assert len(clean_text("x" * 1000, 300)) == 300


@pytest.mark.parametrize("url", BAD_URLS)
def test_safe_url_rejects_dangerous_urls(url):
    assert safe_url(url) == ""


def test_safe_url_keeps_normal_links():
    assert safe_url("https://jobs.example.com/offer?id=1&x=2") == "https://jobs.example.com/offer?id=1&x=2"
    assert safe_url("http://example.com/a") == "http://example.com/a"


def test_scraped_offer_is_cleaned():
    target = Target(name="Bank", type="intl_bank", platform="generic", careers_url="https://bank.example")
    raw = RawJob(title='Structuring Intern <img src=x onerror="alert(1)"> - Summer 2027',
                 url="https://bank.example/jobs/1", location="<script>alert(1)</script>Paris, France")
    record = to_record(target, raw)
    assert record is not None
    assert "<" not in record["title"] and "onerror" not in record["title"]
    assert record["location"] == "Paris, France"
    raw.url = "javascript:alert(1)"
    assert to_record(target, raw) is None      # an offer without a safe link is dropped


class FakeHttp:
    def __init__(self, body):
        self.body = body

    def get(self, url, **kwargs):
        class Resp:
            content = self.body.encode()
        return Resp()


def test_rss_entries_are_cleaned_and_bad_links_dropped():
    rss = """<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
    <item><title>&lt;script&gt;alert(1)&lt;/script&gt;Taux BCE</title><link>https://ok.example/a</link>
      <description><![CDATA[<img src=x onerror=alert(1)>Résumé <b>gras</b>]]></description></item>
    <item><title>Piège</title><link>javascript:alert(1)</link></item>
    <item><title>Piège data</title><link>data:text/html,hi</link></item>
    </channel></rss>"""
    items = feeds.fetch({"name": "Test", "url": "https://feed.example/rss"}, FakeHttp(rss))
    assert [i["link"] for i in items] == ["https://ok.example/a"]
    assert items[0]["title"] == "Taux BCE"
    assert items[0]["summary"] == "Résumé gras"


def test_digest_markdown_is_inert():
    line = notify._line({"score": 80, "title": "[clic](javascript:alert(1)) <img src=x> @someone",
                         "url": "javascript:alert(1)", "employer": "**X**"}, False)
    assert not re.search(r"(?<!\\)\]\(javascript", line)     # the link syntax is escaped
    assert not re.search(r"(?<!\\)<img", line) and "@someone" not in line
    assert "\\*\\*X\\*\\*" in line


def test_analyses_reject_unsafe_source_urls():
    art = {"title": "t", "theme": "central_banks", "lead": "l", "what": "w", "why": "y", "impact": "i",
           "interview": {"question": "q", "hints": []},
           "sources": [{"title": "s", "url": "https://ok.example/\"><script>"}]}
    problems = analyses.validate({"days": [{"date": "2026-10-24", "brief": [], "articles": [art]}]})
    assert any("sources[0]" in p for p in problems)


# ---------------------------------------------------------------- site: static checks

JS_FILES = sorted((ROOT / "docs").glob("*.js"))


@pytest.mark.parametrize("path", JS_FILES, ids=lambda p: p.name)
def test_site_javascript_never_builds_html_from_strings(path):
    code = path.read_text(encoding="utf-8")
    for sink in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function"):
        assert sink not in code, f"{path.name} uses {sink}"
    # Links are only set through setLink() (URL check) or to local blob: downloads.
    for line in re.findall(r".*\.href\s*=.*", code):
        assert "createObjectURL" in line or "a.href = safe;" in line, line.strip()


def test_page_has_strict_csp_and_no_inline_code():
    page = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    csp = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', page).group(1)
    assert "script-src 'self'" in csp and "default-src 'none'" in csp and "object-src 'none'" in csp
    assert "unsafe-inline" not in csp and "unsafe-eval" not in csp
    assert '<meta name="referrer" content="no-referrer">' in page
    assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", page), "inline <script>"
    assert not re.search(r"\son[a-z]+\s*=", page), "inline event handler"
    assert not re.search(r'<script[^>]+src="(https?:)?//', page), "external script"


# ---------------------------------------------------------------- site: browser test

def _hostile_site(tmp_path: Path) -> Path:
    site = tmp_path / "site"
    (site / "data").mkdir(parents=True)
    for f in (ROOT / "docs").iterdir():
        if f.is_file():
            (site / f.name).write_bytes(f.read_bytes())
    evil = '<img src=x onerror="window.__pwned=1"><script>window.__pwned=1</script>'
    job = {"id": "evil-1", "employer": evil, "employer_type": "intl_bank", "platform": "x", "title": evil,
           "location": evil, "countries": ["FR"], "country_names": ["France"], "region": "france", "family": "structuring",
           "role_level": "high", "score": 90, "score_breakdown": {"role": 50, "geo": 30, "city": 5, "timing": 5},
           "timing": "summer", "start": "2027-06", "deadline": "", "deadline_source": "", "url": "javascript:window.__pwned=1",
           "posted_at": "", "first_seen": "2026-10-23", "last_seen": "2026-10-23", "active": True}
    write = lambda name, data: (site / "data" / name).write_text(json.dumps(data), encoding="utf-8")
    write("jobs.json", {"generated_at": "2026-10-23T05:00:00+00:00", "jobs": [job]})
    write("new_today.json", {"jobs": [job]})
    write("errors.json", {"employers_total": 1, "employers_failed": 1, "errors": [
        {"employer": evil, "platform": evil, "error": evil, "careers_url": "javascript:window.__pwned=1"}]})
    article = {"id": "a1", "title": evil, "link": "javascript:window.__pwned=1", "source": evil, "sources": [evil],
               "published": "2099-01-01T00:00", "summary": evil, "themes": ["central_banks"], "official": False,
               "first_seen": "2099-01-01T00:00", "score": 90}
    write("news.json", {"generated_at": "2099-01-01T00:00:00+00:00", "items": [article]})
    write("analyses.json", {"days": [{"date": "2099-01-01", "brief": [evil], "articles": [{
        "title": evil, "theme": "central_banks", "lead": evil, "what": evil, "why": evil, "impact": evil,
        "interview": {"question": evil, "hints": [evil]}, "glossary": [{"term": evil, "definition": evil}],
        "sources": [{"title": evil, "url": "javascript:window.__pwned=1", "source": evil}]}]}]})
    (site / "formations.json").write_text(json.dumps({"categories": {"marches": "Marchés"}, "formations": [{
        "id": "evil", "nom": evil, "organisme": evil, "categorie": "marches", "priorite": 1, "heures": None, "cout": evil,
        "lien": "javascript:window.__pwned=1", "competences": [evil], "utilite": evil, "echeance": None,
        "echeance_libelle": evil, "verifie_le": None, "a_verifier": [evil], "cv": ""}]}), encoding="utf-8")
    return site


def test_hostile_data_does_not_execute_in_the_browser(tmp_path):
    playwright = pytest.importorskip("playwright.sync_api")
    site = _hostile_site(tmp_path)
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(site)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}/"
    try:
        with playwright.sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except Exception:
                exe = next(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome"), None)
                if not exe:
                    pytest.skip("no Chromium available")
                browser = p.chromium.launch(executable_path=str(exe))
            page = browser.new_page()
            dialogs = []
            page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))
            page.goto(base)
            page.wait_for_selector(".card")
            for tab in ("new", "all", "news", "formations"):
                page.click(f'[data-tab="{tab}"]')
                page.wait_for_timeout(300)
                if tab == "news":
                    for view in ("analyses", "today", "week"):
                        page.click(f'[data-nview="{view}"]')
                        page.wait_for_timeout(150)
                for link in page.query_selector_all("a"):
                    href = (link.get_attribute("href") or "").lower()
                    assert not href.startswith(("javascript:", "data:", "vbscript:")), href
                    if link.get_attribute("target") == "_blank":
                        assert "noopener" in (link.get_attribute("rel") or "")
                # Click every link that kept no href: nothing must run.
                for link in page.query_selector_all("a:not([href])"):
                    if link.is_visible():
                        link.click()
            assert page.evaluate("window.__pwned") is None
            assert page.evaluate("document.querySelectorAll('img[onerror], script:not([src])').length") == 0
            assert page.evaluate("document.body.textContent.includes('<script>')")   # shown as text, not run
            assert dialogs == []
            browser.close()
    finally:
        server.shutdown()
