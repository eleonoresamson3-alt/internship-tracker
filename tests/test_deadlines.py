from datetime import date

import pytest

from tracker.deadlines import estimate, parse
from tracker.timing import analyse

OCT_2026 = date(2026, 10, 23)


@pytest.mark.parametrize("text,expected", [
    ("Application deadline: 15 November 2026.", date(2026, 11, 15)),
    ("Applications close on November 30, 2026", date(2026, 11, 30)),
    ("Date limite de candidature : 30/11/2026", date(2026, 11, 30)),
    ("Candidatures jusqu'au 1er décembre 2026", date(2026, 12, 1)),
    ("Closing date 2026-12-05", date(2026, 12, 5)),
    ("Bewerbungsschluss: 10. Januar 2027", None),  # "10." is not supported, no false date
    ("We start interviews in November 2026.", None),
    ("", None),
])
def test_parse(text, expected):
    assert parse(text) == expected


def test_estimate_international_bank_summer():
    # Summer 2027 at an international bank: usual window closes end of November 2026.
    assert estimate("intl_bank", analyse("2027 Summer Analyst - Markets"), OCT_2026) == date(2026, 11, 30)


def test_estimate_french_bank_june_start():
    assert estimate("french_bank", analyse("Stage Structuration - Juin 2027"), OCT_2026) == date(2027, 4, 30)


def test_estimate_none_for_institutions_and_past_windows():
    assert estimate("institution", analyse("Traineeship 2027"), OCT_2026) is None
    # Trading firms usually close summer recruiting at the end of October.
    assert estimate("hedge_fund", analyse("Summer 2027 Quant Intern"), OCT_2026) == date(2026, 10, 31)
    assert estimate("hedge_fund", analyse("Summer 2027 Quant Intern"), date(2026, 11, 15)) is None
