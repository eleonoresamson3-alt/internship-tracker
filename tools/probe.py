"""Temporary: test candidate news feeds and calendar pages (removed after use)."""
import re, sys
import feedparser
from bs4 import BeautifulSoup
from tracker.http import PoliteClient

FEEDS = [
    "https://services.lesechos.fr/rss/les-echos-economie.xml",
    "https://services.lesechos.fr/rss/les-echos-marches.xml",
    "https://www.lesechos.fr/rss/rss_finance-marches.xml",
    "https://www.imf.org/en/News/RSS?Language=ENG",
    "https://www.imf.org/en/Publications/RSS?language=eng",
    "https://www.ft.com/global-economy?format=rss",
    "https://www.ft.com/rss/home",
    "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "https://feeds.content.dowjones.io/public/rss/mw_marketpulse",
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258",
    "https://www.investing.com/rss/news.rss",
    "https://fr.investing.com/rss/news.rss",
    "https://www.ecb.europa.eu/rss/blog.html",
    "https://www.federalreserve.gov/feeds/press_monetary.xml",
    "https://www.bankofengland.co.uk/rss/news",
    "https://www.banque-france.fr/fr/rss.xml",
    "https://www.banque-france.fr/rss.xml",
    "https://www.esma.europa.eu/rss.xml",
    "https://www.agefi.fr/rss",
    "https://www.agefi.fr/rss.xml",
    "https://www.boursorama.com/rss/actualites/economie",
    "https://www.zonebourse.com/rss/",
    "https://www.lemonde.fr/economie/rss_full.xml",
    "https://www.latribune.fr/feed.xml",
    "https://www.lefigaro.fr/rss/figaro_economie.xml",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://www.risk.net/feeds/rss",
]
PAGES = [  # look for alternate RSS links
    "https://www.amf-france.org/fr/abonnements-flux-rss",
    "https://www.lesechos.fr/rss",
    "https://www.agefi.fr/",
    "https://www.banque-france.fr/fr/communiques-de-presse",
    "https://www.zonebourse.com/",
]
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
for url in ["https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html",
            "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"]:
    try:
        r = http.get(url, retries=0)
        s = BeautifulSoup(r.text, "html.parser")
        text = s.get_text(" ", strip=True)
        print(f"CAL {url} len={len(r.text)}")
        i = text.find("2026")
        print("   ", text[max(0, i-300):i+1500])
        if "ecb" in url:
            for dl in s.select("dl, .definition-list, dt")[:3]:
                print("   HTML:", str(dl)[:1500])
        else:
            for p in s.select(".panel.panel-default")[:2]:
                print("   HTML:", str(p)[:2500])
    except Exception as e:
        print(f"CAL ERR {url} | {type(e).__name__}: {str(e)[:120]}")
