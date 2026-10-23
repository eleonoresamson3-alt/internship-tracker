"""Temporary: explore the Webstat API with the WEBSTAT_API_KEY secret (removed after use)."""
import builtins, json, os
from tracker.http import PoliteClient
OUT = []
def say(*a): OUT.append(" ".join(str(x) for x in a))
http = PoliteClient()
H = {"Authorization": f"Apikey {os.environ.get('WEBSTAT_API_KEY', '').strip()}"}
B = "https://webstat.banque-france.fr/api/explore/v2.1/catalog/datasets"
def get(path, **params):
    try:
        r = http.session.get(B + path, params=params, headers=H, timeout=60)
        say("GET", path, params, "->", r.status_code)
        return r.json()
    except Exception as e:
        say("ERR", path, type(e).__name__, str(e)[:200]); return None
r = get("/series/records", where='search("Echeance Constante") and series_key like "FM.D.%"', limit=40, select="series_key,title_fr")
if r: say("TEC", r.get("total_count"), json.dumps(r.get("results"), ensure_ascii=False)[:3000])
r = get("/series/records", where='search("Echéance Constante")', limit=60, select="series_key,title_fr")
if r: say("TEC2", r.get("total_count"), json.dumps([x["series_key"] for x in r.get("results", [])], ensure_ascii=False)[:3000])
for k in ["FM.D.FR.EUR.FR2.BB.FRMOYTEC10.HSTA", "FM.D.FR.EUR.FR2.BB.FRMOYTEC2.HSTA"]:
    r = get("/observations/records", where=f'series_key="{k}"', order_by="time_period_start desc", limit=3, select="time_period_start,obs_value")
    if r: say("OBS", k, json.dumps(r, ensure_ascii=False)[:500])
    r = get("/observations/exports/json", where=f'series_key="{k}"', limit=5)
    if r is not None: say("EXPORT", k, type(r).__name__, json.dumps(r, ensure_ascii=False)[:300])
text = "\n".join(OUT)
for n, i in enumerate(range(0, len(text), 3500)):
    builtins.print(f"::notice title=Probe {n}::" + text[i:i+3500].replace("%", "%25").replace("\r", "").replace("\n", "%0A"))
