"""Temporary: read official training pages (removed after use)."""
import builtins, re
from bs4 import BeautifulSoup
from tracker.http import PoliteClient
OUT = []
def say(*a): OUT.append(" ".join(str(x) for x in a))
http = PoliteClient()
PAGES = {
 "FRM fees": ("https://www.garp.org/frm/fees-payments", r"USD|\$|2027|Early|Standard|Enrollment|deadline"),
 "FRM program": ("https://www.garp.org/frm/program-exams", r"hours|Part I|2027|exam"),
 "CFA L1": ("https://www.cfainstitute.org/programs/cfa-program/exam/level-i", r"USD|\$|hours|2027|deadline|fee"),
 "CFA fees": ("https://www.cfainstitute.org/programs/cfa-program/register", r"USD|\$|2027|deadline|fee"),
 "CFA fees2": ("https://www.cfainstitute.org/programs/cfa-program/candidate-resources/exam-fees", r"USD|\$|2027|deadline|fee"),
 "BMC": ("https://www.bloomberg.com/professional/product/bloomberg-market-concepts/", r"\$|hours|module|free|certificate"),
 "BMC2": ("https://portal.bloombergforeducation.com/", r"\$|hours|module|free|certificate|BMC"),
 "Columbia": ("https://www.coursera.org/specializations/financialengineering", r"hours|weeks|months|course|level|Financial Engineering"),
 "Python HKUST": ("https://www.coursera.org/learn/python-statistics-financial-analysis", r"hours|week|level|Python"),
 "Kaggle SQL": ("https://www.kaggle.com/learn/intro-to-sql", r"hours|hrs|lessons|SQL"),
 "Kaggle ASQL": ("https://www.kaggle.com/learn/advanced-sql", r"hours|hrs|lessons|SQL"),
 "QuantNet C++": ("https://quantnet.com/cplusplus-programming-course/", r"\$|weeks|hours|certificate|Baruch|price|tuition"),
 "Baruch online": ("https://mfe.baruch.cuny.edu/online-programming/", r"\$|weeks|hours|certificate|C\+\+"),
 "AMF certif": ("https://www.amf-france.org/fr/acteurs-et-produits/prestataires-financiers/certification-professionnelle-des-acteurs-de-marche", r"organisme|examen|questions|heures|certifi"),
 "AMF certif2": ("https://www.amf-france.org/fr/formations-et-certifications/certification-professionnelle", r"organisme|examen|questions|heures|certifi"),
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
        if name.startswith("AMF"):
            say("  links:", sorted({a.get("href") for a in soup.find_all("a") if a.get("href") and "certif" in a.get("href")})[:20])
    except Exception as e:
        say(f"== {name} ERR {type(e).__name__}: {str(e)[:160]}")
text = "\n".join(OUT)
for n, i in enumerate(range(0, len(text), 3500)):
    builtins.print(f"::notice title=Probe {n}::" + text[i:i+3500].replace("%", "%25").replace("\r", "").replace("\n", "%0A"))
