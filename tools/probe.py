"""Temporary: test candidate news feeds and calendar pages (removed after use)."""
import re, sys, builtins
OUT = []
def print(*a, **k):
    OUT.append(" ".join(str(x) for x in a))
import feedparser
from bs4 import BeautifulSoup
from tracker.http import PoliteClient

FEEDS = [f"https://www.amf-france.org/fr/flux-rss/display/{n}" for n in range(21, 32)] + [
    "https://www.agefi.fr/index.rss",
    "https://www.imf.org/en/News/rss?language=eng",
    "https://www.imf.org/external/rss/feeds.aspx?category=WHATSNEW",
    "https://www.imf.org/en/rss-list/feed?category=PRESS",
    "https://www.latribune.fr/entreprises-finance/banques-finance/feed.xml",
    "https://www.latribune.fr/economie/feed.xml",
    "https://www.lemonde.fr/argent/rss_full.xml",
    "https://www.banque-france.fr/fr/rss",
    "https://www.ecb.europa.eu/rss/fie.html",
    "https://www.ft.com/companies/financials?format=rss",
    "https://www.ft.com/alphaville?format=rss",
]
PAGES = ["https://www.imf.org/en/news", "https://www.banque-france.fr/fr", "https://www.imf.org/en/Home/RSS"]
http = PoliteClient()
for url in FEEDS:
    try:
        r = http.get(url, retries=0)
        p = feedparser.parse(r.content)
        print(f"FEED {len(p.entries):3d} {url} | {p.entries[0].get('title','')[:70] if p.entries else r.text[:80]!r}")
    except Exception as e:
        print(f"FEED ERR {url} | {type(e).__name__}: {str(e)[:120]}")
for url in PAGES:
    try:
        r = http.get(url, retries=0)
        s = BeautifulSoup(r.text, "html.parser")
        links = {a.get("href") for a in s.find_all(["a", "link"]) if a.get("href") and re.search(r"rss|feed|xml", a.get("href"), re.I)}
        print(f"PAGE {url} | {sorted(links)[:40]}")
    except Exception as e:
        print(f"PAGE ERR {url} | {type(e).__name__}: {str(e)[:120]}")

text = "\n".join(OUT)
for n, i in enumerate(range(0, len(text), 3500)):
    chunk = text[i:i+3500].replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    builtins.print(f"::notice title=Probe {n}::{chunk}")
