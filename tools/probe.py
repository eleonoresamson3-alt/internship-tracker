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
def raw(url):
    try:
        t = http.get(url, retries=0).text
        say("RAW", url, "|", t[:400].replace("\n", " / "))
    except Exception as e:
        say("ERR", url, type(e).__name__, str(e)[:150])
r = ws("/series/records", where='dataset_id="ECOFI"', limit=100, select="series_key,title_fr")
say("ECOFI", r.get("total_count"), json.dumps([(x["series_key"], x.get("title_fr")) for x in r.get("results", [])], ensure_ascii=False)[:3000])
for q in ["XAU", "cours de l'or", "prix de l'or", "Euro Stoxx", "EuroStoxx", "DJ Euro", "Dow Jones", "SBF", "volatilité implicite"]:
    r = ws("/series/records", where=f'search("{q}")', limit=10, select="series_key,title_fr")
    say("WS", q, r.get("total_count"), json.dumps([(x["series_key"], x.get("title_fr")) for x in r.get("results", [])], ensure_ascii=False)[:800])
r = ws("/observations/records", where='series_key="ECOFI.SPI.FR.FPE_IX._Z.D"', order_by="time_period_start desc", limit=3, select="time_period_start,obs_value")
say("CAC obs", json.dumps(r)[:300])
for key in ["BBEX3/D.XAU.USD.CA.AC.C05", "BBEX3/D.XAU.USD.CA.AA.C05", "BBEX3/D.XAU.EUR.CA.AC.C05", "BBEX3/D.XAU.USD.EA.AA.C05"]:
    f, k = key.split("/", 1)
    raw(f"https://api.statistiken.bundesbank.de/rest/download/{f}/{k}?format=csv&lang=en&lastNObservations=3")
raw("https://api.statistiken.bundesbank.de/rest/metadata/dataflow/BBK/BBEX3")
text = "\n".join(OUT)
for n, i in enumerate(range(0, len(text), 3500)):
    builtins.print(f"::notice title=Probe {n}::" + text[i:i+3500].replace("%", "%25").replace("\r", "").replace("\n", "%0A"))
