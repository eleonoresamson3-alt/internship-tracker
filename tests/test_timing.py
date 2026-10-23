import pytest

from tracker.timing import analyse


@pytest.mark.parametrize("title,description,kind,start", [
    ("Stage - Analyste Produits Structurés – Mars 2027", "", "off-cycle", "2027-03"),
    ("2027 Summer Internship - Markets", "", "summer", "2027"),
    ("Off-cycle Internship 2028", "", "off-cycle", "2028"),
    ("Structuring Intern - June 2027", "", "summer", "2027-06"),
    ("Stage - FOREX Officer H/F", "Le stage débutera en janvier 2027 pour 6 mois.", "off-cycle", "2027-01"),
    ("Quant Intern", "Start date: June 2027. Applications close May 2027.", "summer", "2027-06"),
    ("Praktikum Marktrisiko", "ab Juni 2027 für 6 Monate", "summer", "2027-06"),
    ("Stage Structuration", "You may apply now.", "unknown", ""),
])
def test_analyse(title, description, kind, start):
    t = analyse(title, description)
    assert (t.kind, t.start) == (kind, start)


def test_six_months():
    assert analyse("Stage 6 mois - Pricing").six_months
    assert not analyse("Summer Analyst").six_months
