"""Temporary: read official training pages (removed after use)."""
import builtins, re
from bs4 import BeautifulSoup
from tracker.http import PoliteClient
OUT = []
def say(*a): OUT.append(" ".join(str(x) for x in a))
http = PoliteClient()
PAGES = {
 "CFA exam": ("https://www.cfainstitute.org/en/programs/cfa/exam", r"USD|\$|hours|2027|deadline|fee|Level I"),
 "CFA prog exam": ("https://www.cfainstitute.org/programs/cfa-program/exam", r"USD|\$|hours|2027|deadline|fee|Level I"),
 "CFA fees": ("https://www.cfainstitute.org/programs/cfa-program/exam/fees", r"USD|\$|2027|deadline|fee"),
 "CFA fees b": ("https://www.cfainstitute.org/programs/cfa-program/fees", r"USD|\$|2027|deadline|fee"),
 "CFA dates": ("https://www.cfainstitute.org/programs/cfa-program/exam/dates", r"2027|deadline|Level I"),
 "CFA L1": ("https://www.cfainstitute.org/programs/cfa-program/levels/level-i", r"USD|\$|hours|2027|Level I"),
 "QuantNet courses": ("https://quantnet.com/courses", r"\$|weeks|C\+\+|tuition|certificate"),
 "AMF home": ("https://www.amf-france.org/fr", r"certification"),
}
for name, (url, pat) in PAGES.items():
    try:
        r = http.get(url, retries=0)
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script", "style", "noscript"]): t.decompose()
        text = " ".join(soup.get_text(" ").split())
        hits = []
        for m in re.finditer(pat, text):
            s = text[max(0, m.start()-120): m.end()+160]
            if not any(s[:60] in h for h in hits): hits.append(s)
            if len(hits) >= 10: break
        say(f"== {name} {url} len={len(text)}")
        for h in hits: say("  ·", h)
        if name.startswith("AMF") or name.startswith("CFA"):
            say("  links:", sorted({a.get("href") for a in soup.find_all("a") if a.get("href") and re.search(r"certif|fee|exam|level", a.get("href"))})[:20])
    except Exception as e:
        say(f"== {name} ERR {type(e).__name__}: {str(e)[:160]}")
text = "\n".join(OUT)
for n, i in enumerate(range(0, len(text), 3500)):
    builtins.print(f"::notice title=Probe {n}::" + text[i:i+3500].replace("%", "%25").replace("\r", "").replace("\n", "%0A"))
