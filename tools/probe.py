"""Temporary: look for free French yield sources without an account (removed after use)."""
import re, builtins
from bs4 import BeautifulSoup
from tracker.http import PoliteClient
OUT = []
def say(*a): OUT.append(" ".join(str(x) for x in a))
http = PoliteClient()
DATA = [
    "https://data-api.ecb.europa.eu/service/data/IRS/M.FR.L.L40.CI.0000.EUR.N.Z?format=csvdata&lastNObservations=3",
    "https://data-api.ecb.europa.eu/service/data/FM/D.FR.EUR.4F.BB.FR10YT_RR.YLD?format=csvdata&lastNObservations=3",
    "https://data-api.ecb.europa.eu/service/data/FM/D.FR.EUR.4F.BB.FR2YT_RR.YLD?format=csvdata&lastNObservations=3",
    "https://data-api.ecb.europa.eu/service/data/FM?format=csvdata&lastNObservations=1&detail=serieskeysonly",
    "https://fred.stlouisfed.org/graph/fredgraph.csv?id=IRLTLT01FRM156N&cosd=2026-01-01",
    "https://webstat.banque-france.fr/fr/",
    "https://www.aft.gouv.fr/",
    "https://www.aft.gouv.fr/fr/taux-references",
    "https://www.banque-france.fr/fr/statistiques/taux-et-cours/taux-indicatifs-des-bons-du-tresor-et-oat",
    "https://www.banque-france.fr/fr/statistiques/taux-et-cours",
]
for url in DATA:
    try:
        r = http.get(url, retries=0)
        t = r.text
        if "<html" in t[:500].lower():
            s = BeautifulSoup(t, "html.parser")
            links = sorted({a.get("href") for a in s.find_all("a") if a.get("href") and re.search(r"taux|oat|rendement|csv|xls|export|yield", a.get("href") + a.get_text(), re.I)})
            say("PAGE", url, "|", links[:40])
        elif "serieskeysonly" in url:
            keys = [l.split(",")[0] for l in t.splitlines() if ".FR." in l or "FR10" in l or "FR2" in l]
            say("FMKEYS", len(t.splitlines()), keys[:40])
        else:
            say("DATA", url, "|", t[:400].replace("\n", " / "))
    except Exception as e:
        say("ERR", url, "|", type(e).__name__, str(e)[:150])
text = "\n".join(OUT)
for n, i in enumerate(range(0, len(text), 3500)):
    builtins.print(f"::notice title=Probe {n}::" + text[i:i+3500].replace("%", "%25").replace("\r", "").replace("\n", "%0A"))
