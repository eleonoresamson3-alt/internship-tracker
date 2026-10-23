from datetime import datetime, timezone

from tracker.news.classify import score, themes_of
from tracker.news.dedupe import cluster, merge_history, similar

NOW = datetime(2026, 10, 23, 8, tzinfo=timezone.utc)


def test_themes_french_and_english():
    assert themes_of("La BCE abaisse ses taux directeurs de 25 points de base")[0] == "central_banks"
    assert themes_of("Fed holds rates steady as Powell signals patience")[0] == "central_banks"
    assert "structured" in themes_of("Le marché des produits structurés autocall bat des records")
    assert "vol_derivatives" in themes_of("VIX jumps as options traders hedge equity exposure")
    assert "credit_sovereign" in themes_of("Le spread OAT-Bund se tend après la dégradation de la note")
    assert "fx_commodities" in themes_of("Brent crude falls as OPEC raises output")
    assert "regulation" in themes_of("FRTB : l'EBA repousse l'entrée en vigueur")
    assert themes_of("Le Louvre accueille une nouvelle exposition") == []
    # "hedge fund" is not hedging, and English "actions" are not equities.
    t = themes_of("UK waters down rules", "Regulatory regime behind actions against a hedge fund owner")
    assert t[0] == "regulation" and "vol_derivatives" not in t and "equities" not in t


def test_title_counts_more_than_summary():
    themes = themes_of("Volatility spikes on equity markets", "Stocks fell in Paris and Frankfurt")
    assert themes[0] == "vol_derivatives"


def test_score_priorities():
    deriv = score(themes_of("Structured products issuance hits record"))
    equities = score(themes_of("Wall Street stocks close higher"))
    assert deriv > equities
    assert score(["central_banks"], n_sources=3) > score(["central_banks"], n_sources=1)
    assert score(["central_banks"], official=True) > score(["central_banks"])
    assert score([]) == 5


def test_similar_titles():
    assert similar("ECB cuts interest rates by 25 basis points", "ECB cuts rates by 25 basis points in June")
    assert not similar("ECB cuts interest rates", "Fed raises interest rates")
    assert not similar("Markets", "Markets")  # too short to decide


def test_cluster_groups_same_story():
    items = [{"title": "ECB cuts interest rates by 25 basis points"},
             {"title": "ECB cuts rates by 25 basis points, Lagarde says"},
             {"title": "Oil prices fall on OPEC output decision"}]
    groups = cluster(items)
    assert len(groups) == 2 and len(groups[0]) == 2


def test_merge_history_merges_sources_and_prunes():
    old = {"id": "a", "title": "ECB cuts interest rates by 25 basis points", "sources": ["BCE"], "score": 50,
           "published": "2026-10-20T10:00", "first_seen": "2026-10-20T10:00"}
    stale = {"id": "z", "title": "Old story about bonds markets today", "sources": ["FT"], "score": 30,
             "published": "2026-09-01T10:00", "first_seen": "2026-09-01T10:00"}
    fresh = {"id": "b", "title": "ECB cuts rates by 25 basis points again", "sources": ["Les Echos"], "score": 50,
             "published": "2026-10-23T07:00", "first_seen": "2026-10-23T07:00"}
    merged = merge_history([old, stale], [fresh], NOW)
    assert [m["id"] for m in merged] == ["a"]
    assert merged[0]["sources"] == ["BCE", "Les Echos"]


# ---------------------------------------------------------------- calendar

from tracker.news import calendar as cal

ECB_HTML = """<div class="definition-list -zebra"><dl>
<dt> 28/10/2026 </dt><dd> Governing Council of the ECB: monetary policy meeting in Frankfurt (Day 1)<br/></dd>
<dt> 29/10/2026 </dt><dd> Governing Council of the ECB: monetary policy meeting in Frankfurt (Day 2), followed by press conference</dd>
<dt> 29/10/2026 </dt><dd> Press conference following the Governing Council meeting of the ECB in Frankfurt</dd>
<dt> 25/11/2026 </dt><dd> Governing Council of the ECB: non-monetary policy meeting (in Frankfurt)</dd>
<dt> 26/11/2026 </dt><dd> General Council meeting of the ECB in Frankfurt</dd>
<dt> 16/12/2026 </dt><dd> Governing Council of the ECB: monetary policy meeting in Frankfurt (Day 1)</dd>
<dt> 17/12/2026 </dt><dd> Governing Council of the ECB: monetary policy meeting in Frankfurt (Day 2), followed by press conference</dd>
</dl></div>"""

FED_HTML = """<div class="panel panel-default"><div class="panel-heading"><h4><a id="1">2026 FOMC Meetings</a></h4></div>
<div class="row fomc-meeting"><div class="fomc-meeting__month"><strong>October</strong></div>
<div class="fomc-meeting__date">27-28</div></div>
<div class="row fomc-meeting"><div class="fomc-meeting__month"><strong>Dec</strong></div>
<div class="fomc-meeting__date">8-9*</div></div>
<div class="row fomc-meeting"><div class="fomc-meeting__month"><strong>Apr/May</strong></div>
<div class="fomc-meeting__date">30-1</div></div>
<div class="row fomc-meeting"><div class="fomc-meeting__month"><strong>March</strong></div>
<div class="fomc-meeting__date">9 (unscheduled)</div></div>
</div>"""


def test_parse_ecb_groups_two_day_meetings_and_skips_other_meetings():
    got = cal.parse_ecb(ECB_HTML)
    assert [(m["date"], m["end"]) for m in got] == [("2026-10-28", "2026-10-29"), ("2026-12-16", "2026-12-17")]
    assert all(m["bank"] == "BCE" and m["source"] == "official" for m in got)


def test_parse_fed_handles_projections_cross_month_and_unscheduled():
    got = cal.parse_fed(FED_HTML)
    assert [(m["date"], m["end"]) for m in got] == [
        ("2026-04-30", "2026-05-01"), ("2026-10-27", "2026-10-28"), ("2026-12-08", "2026-12-09")]
    assert "SEP" in got[2]["note"] and got[1]["note"] == ""


def test_calendar_falls_back_to_manual_list():
    class Broken:
        def get(self, url):
            raise OSError("down")
    manual = [{"bank": "Fed", "date": "2026-12-08", "end": "2026-12-09"}]
    meetings, errors = cal.fetch_all(manual, Broken())
    assert [(m["bank"], m["source"]) for m in meetings] == [("Fed", "manual")]
    assert {e["source"] for e in errors} == {"Calendrier BCE", "Calendrier Fed"}


def test_analyst_coverage_is_not_hedging():
    assert "vol_derivatives" not in themes_of("Needham initie une couverture de Diodes avec une recommandation d'achat")
    assert "vol_derivatives" in themes_of("Les entreprises renforcent leur couverture de change")


# ---------------------------------------------------------------- market changes

from datetime import date

from tracker.news.market import changes


def test_rate_changes_in_basis_points_and_prices_in_percent():
    pts = [(date(2026, 9, 1), 3.0), (date(2026, 10, 15), 3.1), (date(2026, 10, 22), 3.2), (date(2026, 10, 23), 3.25)]
    c = changes(pts, "%")
    assert (c["d1"], c["w1"], c["m1"]) == (5.0, 15.0, 25.0)
    assert changes([(date(2026, 10, 22), 100.0), (date(2026, 10, 23), 101.0)], "pts")["d1"] == 1.0


def test_step_series_holds_its_value_until_the_next_change():
    pts = [(date(2026, 6, 11), 2.25), (date(2026, 9, 16), 2.5)]
    c = changes(pts, "%", step=True, today=date(2026, 10, 10))
    assert (c["value"], c["date"], c["d1"], c["w1"], c["m1"]) == (2.5, "2026-10-10", 0.0, 0.0, 25.0)


# ---------------------------------------------------------------- analyses

from tracker.news import analyses


def _article(**over):
    art = {"title": "La BCE maintient ses taux", "theme": "central_banks", "lead": "Statu quo attendu.",
           "what": "Le taux de dépôt reste à 2,50 %.", "why": "L'inflation reste au-dessus de la cible.",
           "impact": "Courbe plus pentue, volatilité des taux en baisse.",
           "interview": {"question": "Quel impact sur un autocall ?", "hints": ["taux", "coût de la protection"]},
           "sources": [{"title": "Communiqué", "url": "https://www.ecb.europa.eu/press/x.html", "source": "BCE"}]}
    art.update(over)
    return art


def test_valid_analyses_pass():
    data = {"days": [{"date": "2026-10-24", "brief": ["Statu quo BCE"], "articles": [_article()]}]}
    assert analyses.validate(data) == []


def test_invalid_analyses_are_reported():
    data = {"days": [{"date": "24/10/2026", "articles": [_article(theme="sport", sources=[{"url": "http://x"}])]}]}
    problems = " ".join(analyses.validate(data))
    assert "date" in problems and "theme" in problems and "sources[0]" in problems
    assert analyses.validate({"days": [{"date": "2026-10-24", "articles": []}]})


def test_prune_keeps_recent_days_newest_first():
    data = {"days": [{"date": "2026-08-01"}, {"date": "2026-10-20"}, {"date": "2026-10-23"}]}
    kept = analyses.prune(data, today=date(2026, 10, 24))
    assert [d["date"] for d in kept["days"]] == ["2026-10-23", "2026-10-20"]


def test_parse_webstat_rows_and_missing_key(monkeypatch):
    from tracker.news import market
    rows = [{"series_key": "X", "time_period_start": "2026-10-22", "obs_value": 3.41},
            {"series_key": "X", "time_period_start": "2026-10-21", "obs_value": "3.38"},
            {"series_key": "X", "time_period_start": "2026-10-20", "obs_value": None}]
    assert market.parse_webstat(rows) == [(date(2026, 10, 21), 3.38), (date(2026, 10, 22), 3.41)]
    monkeypatch.delenv("WEBSTAT_API_KEY", raising=False)
    rows, errors = market.fetch_all([{"key": "fr10y", "label": "France 10 ans", "unit": "%",
                                      "provider": "webstat", "series": "X"}], http=None)
    assert rows[0]["status"] == "indisponible" and "WEBSTAT_API_KEY" in rows[0]["note"] and errors == []
