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
d = get("", limit=100, select="dataset_id")
if d: say("DATASETS", [x.get("dataset_id") for x in d.get("results", [])])
o = get("/observations/records", limit=2)
if o: say("OBS sample", json.dumps(o, ensure_ascii=False)[:1500])
s = get("/series/records", limit=2)
if s: say("SERIES sample", json.dumps(s, ensure_ascii=False)[:2000])
for q in ['search("10 ans")', 'search("OAT")', 'search("FR10YT")', 'search("FR2YT")', 'search("rendement")']:
    r = get("/series/records", where=q, limit=20)
    if r: say("SEARCH", q, r.get("total_count"), json.dumps([{k: v for k, v in x.items() if k in ("series_key", "title_fr", "title_en", "series_name", "dataset_id", "frequency", "title")} or x for x in r.get("results", [])], ensure_ascii=False)[:2500])
r = get("/observations/records", where='series_key like "FM.D.FR%"', limit=5, select="series_key")
if r: say("OBS FM.D.FR", json.dumps(r, ensure_ascii=False)[:1000])
text = "\n".join(OUT)
for n, i in enumerate(range(0, len(text), 3500)):
    builtins.print(f"::notice title=Probe {n}::" + text[i:i+3500].replace("%", "%25").replace("\r", "").replace("\n", "%0A"))
