"""Temporary: free official sources for CAC 40, Euro Stoxx 50, VSTOXX and gold (removed after use)."""
import builtins, json, os
from tracker.http import PoliteClient
OUT = []
def say(*a): OUT.append(" ".join(str(x) for x in a))
http = PoliteClient()
H = {"Authorization": f"Apikey {os.environ.get('WEBSTAT_API_KEY', '').strip()}"}
B = "https://webstat.banque-france.fr/api/explore/v2.1/catalog/datasets"
def ws(path, **params):
    try:
        r = http.session.get(B + path, params=params, headers=H, timeout=60)
        return r.json()
    except Exception as e:
        say("ERR", path, e); return {}
for q in ["CAC", "CAC 40", "Stoxx", "VSTOXX", "or", "gold", "once", "S&P", "indice boursier", "Nikkei", "volatilit"]:
    r = ws("/series/records", where=f'search("{q}")', limit=15, select="series_key,title_fr")
    say("WS", q, r.get("total_count"), json.dumps([(x["series_key"], x.get("title_fr")) for x in r.get("results", [])], ensure_ascii=False)[:1200])
def raw(url):
    try:
        t = http.get(url, retries=0).text
        say("RAW", url, "|", t[:300].replace("\n", " / "))
    except Exception as e:
        say("ERR", url, type(e).__name__, str(e)[:150])
for key in ["FM/D.U2.EUR.DS.EI.DJES50I.HSTA", "FM/D.U2.EUR.DS.EI.DJEURST.HSTA", "FM/D.FR.EUR.DS.EI.FRCAC40.HSTA", "FM/D.U2.EUR.DS.EI.VSTOXXI.HSTA", "FM/D.US.USD.DS.EI.S_PCOMP.HSTA"]:
    f, k = key.split("/", 1)
    raw(f"https://data-api.ecb.europa.eu/service/data/{f}/{k}?format=csvdata&lastNObservations=2")
raw("https://data-api.ecb.europa.eu/service/data/FM/D..EUR.DS.EI..HSTA?format=csvdata&lastNObservations=1&detail=serieskeysonly")
for key in ["BBEX3/D.XAU.USD.EA.AC.C05", "BBEX3/D.XAU.USD.EA.AC.C04", "BBEX3/D.XAU.EUR.EA.AC.C05"]:
    f, k = key.split("/", 1)
    raw(f"https://api.statistiken.bundesbank.de/rest/download/{f}/{k}?format=csv&lang=en&lastNObservations=3")
for sid in ["NASDAQCOM", "DJIA", "NIKKEI225", "GOLDPMGBD228NLBM", "PCU2122212122210"]:
    raw(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd=2026-10-01")
text = "\n".join(OUT)
for n, i in enumerate(range(0, len(text), 3500)):
    builtins.print(f"::notice title=Probe {n}::" + text[i:i+3500].replace("%", "%25").replace("\r", "").replace("\n", "%0A"))
