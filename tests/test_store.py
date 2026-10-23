from tracker.store import dedupe, merge, new_today


def job(id_, title="Structuring Intern", employer="Bank", location="Paris", score=80):
    return {"id": id_, "employer": employer, "title": title, "location": location, "score": score}


def test_dedupe_same_title_and_location():
    jobs = dedupe([job("a"), job("b", title="Structuring  intern"), job("c", location="London")])
    assert sorted(j["id"] for j in jobs) in (["a", "c"], ["b", "c"])


def test_merge_first_seen_and_new_today():
    day1 = merge([], [job("a")], "2027-01-01", set())
    assert day1[0]["first_seen"] == "2027-01-01"
    day2 = merge(day1, [job("a"), job("b", title="Pricing Intern")], "2027-01-02", set())
    by_id = {j["id"]: j for j in day2}
    assert by_id["a"]["first_seen"] == "2027-01-01"
    assert by_id["a"]["last_seen"] == "2027-01-02"
    assert [j["id"] for j in new_today(day2, "2027-01-02")] == ["b"]


def test_missing_offer_becomes_inactive():
    day1 = merge([], [job("a")], "2027-01-01", set())
    day2 = merge(day1, [], "2027-01-02", set())
    assert day2[0]["active"] is False


def test_failed_employer_keeps_offers_active():
    day1 = merge([], [job("a")], "2027-01-01", set())
    day2 = merge(day1, [], "2027-01-02", {"Bank"})
    assert day2[0]["active"] is True


def test_reposted_offer_keeps_first_seen():
    day1 = merge([], [job("a")], "2027-01-01", set())
    day2 = merge(day1, [job("a2")], "2027-01-05", set())
    assert len(day2) == 1
    assert day2[0]["id"] == "a2" and day2[0]["first_seen"] == "2027-01-01"


def test_prune_old_inactive():
    day1 = merge([], [job("a")], "2027-01-01", set())
    later = merge(day1, [], "2027-03-15", set())
    assert later == []
