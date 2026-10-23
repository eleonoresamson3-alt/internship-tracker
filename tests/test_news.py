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
