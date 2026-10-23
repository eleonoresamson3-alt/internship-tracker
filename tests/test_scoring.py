from tracker.scoring import role_match, score


def test_role_levels():
    assert role_match("Structuring Intern")[0] == "high"
    assert role_match("Stage Structuration Actions")[0] == "high"
    assert role_match("Intern - Pricing & XVA")[0] == "high"
    assert role_match("Stage Validation de modèles")[0] == "high"
    assert role_match("Stage Risque de marché")[0] == "high"
    assert role_match("Quantitative Researcher Intern")[0] == "high"
    assert role_match("Stage Dérivés de taux")[0] == "high"
    assert role_match("Quant Developer Intern")[0] == "medium"
    assert role_match("Strats Summer Analyst")[0] == "medium"
    assert role_match("Trading Intern")[0] == "medium"
    assert role_match("Product Control Intern")[0] == "medium"
    assert role_match("Global Markets Sales Intern")[0] == "low"
    assert role_match("Stage Gestion d'actifs")[0] == "low"
    assert role_match("HR Business Partner Intern")[0] == "none"
    # M&A / investment banking is not a markets role.
    assert role_match("Global Investment Banking Analyst Program - Off-Cycle Internship")[0] == "none"
    assert role_match("Commercial & Investment Banking - Global Markets - Off-cycle Internship")[0] == "low"


def test_role_families():
    assert role_match("Structuring Intern")[1] == "Structuring"
    assert role_match("Model Validation Intern")[1] == "Risk"
    assert role_match("Trading Intern")[1] == "Trading"


def test_description_is_ignored_for_the_role():
    assert score("Software Engineer Intern", "London", ["GB"], "Build our trading systems").total == 0


def test_geography_ordering():
    paris = score("Structuring Intern", "Paris, France", ["FR"]).total
    lux = score("Structuring Intern", "Luxembourg", ["LU"]).total
    lisbon = score("Structuring Intern", "Lisbon, Portugal", ["PT"]).total
    ny = score("Structuring Intern", "New York, NY", ["US"]).total
    assert paris > lux > lisbon > ny


def test_role_dominates_geography():
    # A high-priority role abroad beats a low-priority role in France.
    assert score("Structuring Intern", "New York", ["US"]).total > \
        score("Sales Intern", "Paris", ["FR"]).total


def test_multi_location_uses_best_country():
    s = score("Pricing Intern", "London; Paris", ["GB", "FR"])
    assert s.region == "France"


def test_no_markets_signal_scores_zero():
    assert score("Marketing Intern", "Paris", ["FR"]).total == 0


def test_timing_bonus():
    base = score("Structuring Intern", "Madrid", ["ES"]).total
    off = score("Structuring Off-Cycle Intern (6 months)", "Madrid", ["ES"]).total
    assert off > base


def test_score_is_capped():
    s = score("Structuring Off-cycle Internship 2027 6 months", "Paris, La Défense", ["FR"])
    assert s.total <= 100
