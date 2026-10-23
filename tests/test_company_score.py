from tracker.company_score import score


def test_ordering_matches_targets():
    natixis, _ = score("Natixis CIB", "french_bank")
    leonteq, _ = score("Leonteq", "broker")
    blackrock, _ = score("BlackRock", "asset_manager")
    danone, _ = score("Danone", "corporate")
    assert natixis > blackrock > danone
    assert leonteq > blackrock


def test_reasons():
    points, reasons = score("Natixis CIB", "french_bank")
    assert reasons == ["Structuring / pricing reconnu", "France"]
    assert score("Helaba", "european_bank")[1] == ["Europe"]
    assert score("Unknown Co", "unknown_type") == (10, [])
