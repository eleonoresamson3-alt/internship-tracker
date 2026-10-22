import pytest

from tracker.geo import detect_countries, normalize_country, region_of


@pytest.mark.parametrize("location,expected", [
    ("Paris, France", ["FR"]),
    ("La Défense", ["FR"]),
    ("London, United Kingdom", ["GB"]),
    ("London, UK", ["GB"]),
    ("Zürich", ["CH"]),
    ("Genève, Suisse", ["CH"]),
    ("Luxembourg", ["LU"]),
    ("Frankfurt am Main, DE", ["DE"]),
    ("New York, NY", ["US"]),
    ("Chicago, IL", ["US"]),
    ("Hong Kong", ["HK"]),
    ("Bruxelles", ["BE"]),
    ("Milano", ["IT"]),
])
def test_detect_countries(location, expected):
    assert detect_countries(location) == expected


def test_multiple_countries():
    assert set(detect_countries("Paris; London; New York")) == {"FR", "GB", "US"}


def test_empty():
    assert detect_countries("") == []


def test_normalize_country():
    assert normalize_country("fr") == "FR"
    assert normalize_country("GBR") == "GB"
    assert normalize_country("United States") == "US"
    assert normalize_country("UK") == "GB"


def test_regions():
    assert region_of("FR") == "France"
    assert region_of("GB") == "Europe (priority)"
    assert region_of("PT") == "Europe (other)"
    assert region_of("SG") == "Rest of world"
