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
    ("Stage Structuration - Début 2027", "", "off-cycle", "2027-01"),
    ("Off-cycle Internship (Early 2027)", "", "off-cycle", "2027-01"),
    ("Spring 2027 Off-Cycle Internship", "", "off-cycle", "2027-03"),
    ("Markets Intern - Fall 2027", "", "off-cycle", "2027-09"),
    ("Quant Intern", "The internship will start in early 2027.", "off-cycle", "2027-01"),
    ("Quant Intern", "Candidates graduating in early 2027 are welcome.", "unknown", ""),
    # Ranges start with their first month (they used to be read as the last one).
    ("Internship: Real Estate Investment - 6 months (January - June 2027)", "", "off-cycle", "2027-01"),
    ("Deals - Corporate Finance Off-Cycle Internship (Jan - Jun 27)", "", "off-cycle", "2027-01"),
    ("Consulting Off Cycle Internship (Jan - Jun '27)", "", "off-cycle", "2027-01"),
    ("Internship - 6 months (start Jan/Feb2027)", "", "off-cycle", "2027-01"),
    ("Stage de janvier à juin 2027 - Structuration", "", "off-cycle", "2027-01"),
    ("Markets Internship (July - December 2027)", "", "summer", "2027-07"),
    ("Quantitative Trading Intern - Winter Quarter 2027", "", "off-cycle", "2027-01"),
    ("Audit Intern - Winter 2028", "", "off-cycle", "2028-01"),
    ("Structuring Intern - June 2027", "Start date: June 25", "summer", "2027-06"),
    ("Real Estate Finance Intern 2027", "", "unknown", "2027"),
    ("Markets Intern", "Internship period: April - September 2027, Paris.", "off-cycle", "2027-04"),
    ("Stage Structuration", "Durée du stage : de avril à septembre 2027.", "off-cycle", "2027-04"),
    ("Quant Intern", "Applications are reviewed January - March 2027.", "unknown", ""),
    ("Quant Intern", "This 6-month internship is available from April 2027 in Paris.", "off-cycle", "2027-04"),
    ("Stage Pricing", "Date de début : 15/04/2027. Durée 6 mois.", "off-cycle", "2027-04"),
    ("Risk Intern", "Start date: 2027-03-01", "off-cycle", "2027-03"),
    ("Risk Intern", "Start date: 01/04/2027", "unknown", ""),
    ("Rates Structuring Off Cycle Intern 2027",
     "Looking for an intern for the following start dates: January to June 2027, July to December 2027.",
     "off-cycle", "2027-07"),
    ("Risk Intern", "Applications close in March 2027; interviews in April 2027.", "unknown", ""),
    ("Stage estate 2027 - Mercati", "", "summer", "2027"),
])
def test_analyse(title, description, kind, start):
    t = analyse(title, description)
    assert (t.kind, t.start) == (kind, start)


def test_six_months():
    assert analyse("Stage 6 mois - Pricing").six_months
    assert not analyse("Summer Analyst").six_months
