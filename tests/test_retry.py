import pytest
import requests

from tracker import run
from tracker.http import NotJson, _json
from tracker.models import Target


def test_failed_employers_get_a_second_attempt(monkeypatch):
    calls = {}

    def fake(target, http, cache=None):
        calls[target.name] = calls.get(target.name, 0) + 1
        if target.name == "Flaky" and calls["Flaky"] == 1:
            return [], {"employer": "Flaky", "error": "NotJson"}, None, []
        if target.name == "Down":
            return [], {"employer": "Down", "error": "NotJson"}, None, []
        return [{"id": target.name}], None, {"employer": target.name, "fetched": 1, "kept": 1}, []

    monkeypatch.setattr(run, "scrape_one", fake)
    targets = [Target(name=n, type="intl_bank", platform="workday", careers_url="https://x.example") for n in ("Ok", "Flaky", "Down")]
    records, errors, stats = run.scrape(targets, http=None, retry_delay=0.01)
    assert calls == {"Ok": 1, "Flaky": 2, "Down": 2}
    assert [e["employer"] for e in errors] == ["Down"]
    assert {r["id"] for r in records} == {"Ok", "Flaky"}


def test_non_json_answer_gives_a_clear_error():
    resp = requests.Response()
    resp.status_code = 200
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    resp._content = b"<html>Maintenance</html>"
    with pytest.raises(NotJson, match="maintenance"):
        _json(resp)
