import pytest

from datetime import date

from tracker.filters import (corporate_markets_role, description_says_internship, keep, looks_like_internship,
                             out_of_window)

OCT_2026 = date(2026, 10, 23)


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
    "Traineeship in Quantitative Analysis - Directorate General Market Infrastructure",
])
def test_internships_are_kept(title):
    assert keep(title, today=OCT_2026)


@pytest.mark.parametrize("title", [
    "Alternance - Structuration Actions",
    "Apprenti Analyste Risque de Marché",
    "Apprenticeship - Markets Operations",
    "Werkstudent Risikocontrolling",
    "VIE - Structurer Equity Derivatives",
    "Spring Week 2027 - Global Markets",
    "Summer Internship 2025 - Markets",
    "2025 Off-Cycle Internship",
    "Vice President, Structuring",
    "Senior Quantitative Analyst",
    "Internal Audit Analyst",
    "International Sales Associate",
    "Head of Intern Programme",
])
def test_non_internships_are_dropped(title):
    assert not keep(title, today=OCT_2026)


def test_employment_type_counts_as_internship_signal():
    assert looks_like_internship("Equity Derivatives Pricing Analyst", employment_type="Internship")
    assert keep("Equity Derivatives Pricing Analyst", employment_type="Internship")


def test_year_window():
    # In October 2026 with a June 2029 graduation, 2027 to 2029 starts are kept.
    assert out_of_window("Summer 2026 Internship", OCT_2026)
    assert not out_of_window("Summer 2027 Internship", OCT_2026)
    assert not out_of_window("Off-cycle Internship 2028", OCT_2026)
    assert not out_of_window("2029 Spring Off-cycle", OCT_2026)
    assert out_of_window("Summer 2030 Internship", OCT_2026)
    assert not out_of_window("2026/2027 Off-cycle Internship", OCT_2026)
    assert not out_of_window("Off-cycle Internship", OCT_2026)


def test_window_moves_with_time():
    assert not out_of_window("Summer 2026 Internship", date(2026, 3, 1))
    assert out_of_window("Summer 2027 Internship", date(2027, 10, 1))


def test_description_internship_detection():
    assert description_says_internship("Over 10 weeks, interns will work with traders.")
    assert description_says_internship("This summer internship is open to students.")
    assert not description_says_internship("We also run a large internship programme for students.")


def test_corporate_markets_roles():
    assert corporate_markets_role("Stage Trésorerie Groupe - Couverture de change")
    assert corporate_markets_role("Treasury Intern - FX Hedging")
    assert corporate_markets_role("Stage Financement & Trésorerie (6 mois)")
    assert corporate_markets_role("Commodity Risk Analyst Intern")
    assert not corporate_markets_role("Stage Contrôle de gestion")
    assert not corporate_markets_role("Finance Intern - Accounts Payable")
    assert not corporate_markets_role("Stage Audit interne")
    assert not corporate_markets_role("Change Management Intern")
