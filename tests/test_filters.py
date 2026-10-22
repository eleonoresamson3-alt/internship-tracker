import pytest

from tracker.filters import description_says_internship, is_outdated, keep, looks_like_internship


@pytest.mark.parametrize("title", [
    "Structuring Intern - Equity Derivatives",
    "Stage - Structuration Taux (6 mois)",
    "Stagiaire Pricing Crédit",
    "2027 Off-Cycle Internship - Global Markets",
    "Off cycle Intern Quantitative Research",
    "Summer Analyst 2027 - Sales & Trading",
    "Quantitative Trader Internship",
    "Praktikum Marktrisiko (m/w/d)",
    "Tirocinio Risk Management",
    "Prácticas Mercados de Capitales",
    "Market Risk Interns",
    "Stage Actuariat Assurance vie",
])
def test_internships_are_kept(title):
    assert keep(title)


@pytest.mark.parametrize("title", [
    "Alternance - Structuration Actions",
    "Apprenti Analyste Risque de Marché",
    "Apprenticeship - Markets Operations",
    "Werkstudent Risikocontrolling",
    "VIE - Structurer Equity Derivatives",
    "Spring Week 2027 - Global Markets",
    "Summer Internship 2026 - Markets",
    "2025 Off-Cycle Internship",
    "Vice President, Structuring",
    "Senior Quantitative Analyst",
    "Internal Audit Analyst",
    "International Sales Associate",
    "Head of Intern Programme",
])
def test_non_internships_are_dropped(title):
    assert not keep(title)


def test_employment_type_counts_as_internship_signal():
    assert looks_like_internship("Equity Derivatives Pricing Analyst", employment_type="Internship")
    assert keep("Equity Derivatives Pricing Analyst", employment_type="Internship")


def test_years():
    assert is_outdated("Summer 2026 Internship")
    assert not is_outdated("Summer 2027 Internship")
    assert not is_outdated("2026/2027 Off-cycle Internship")
    assert not is_outdated("Off-cycle Internship")


def test_description_internship_detection():
    assert description_says_internship("Over 10 weeks, interns will work with traders.")
    assert description_says_internship("This summer internship is open to students.")
    assert not description_says_internship("We also run a large internship programme for students.")
