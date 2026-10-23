from datetime import date

from tracker.notify import build

TODAY = date(2026, 10, 23)


def job(id_, score, deadline="", source="", active=True):
    return {"id": id_, "title": f"Offer {id_}", "employer": "Bank", "url": "https://x", "score": score,
            "location": "Paris", "deadline": deadline, "deadline_source": source, "active": active}


def test_nothing_to_report():
    assert build([job("a", 90, "2026-12-31", "estimée")], [], TODAY) == ""


def test_close_deadlines_listed_stated_first():
    jobs = [job("est", 80, "2026-10-25", "estimée"), job("ann", 50, "2026-10-28", "annonce"),
            job("low", 20, "2026-10-24", "annonce"), job("gone", 90, "2026-10-24", "annonce", active=False)]
    text = build(jobs, [], TODAY, "owner")
    assert text.startswith("@owner ")
    assert text.index("Offer ann") < text.index("Offer est")
    assert "Offer low" not in text and "Offer gone" not in text


def test_best_new_offers():
    text = build([], [job("n1", 85), job("n2", 40)], TODAY)
    assert "Offer n1" in text and "Offer n2" not in text
