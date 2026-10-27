from datetime import date

from tracker import enrich, run
from tracker.models import RawJob, Target

TARGET = Target(name="Bank", type="intl_bank", platform="generic", careers_url="https://bank.example")

AD_APRIL = """<html><head><script type="application/ld+json">{"@type": "JobPosting", "title": "Markets Intern",
 "description": "<p>Join our team.</p><p>This 6-month internship starts in April 2027 in Paris.</p>"}</script></head></html>"""
AD_JUNE = """<html><body><h1>Markets Intern</h1><p>Start date: June 2027. Duration: 6 months.</p></body></html>"""
AD_NOTHING = """<html><body><h1>Markets Intern</h1><p>Apply before 15 December 2026. Interviews in January 2027.</p></body></html>"""
AD_LD_START = """<script type="application/ld+json">{"@type": "JobPosting", "jobStartDate": "2027-09-01", "description": "x"}</script>"""


class Http:
    def __init__(self, pages):
        self.pages = pages

    def get(self, url, **kwargs):
        page = self.pages[url]

        class Resp:
            text = page
        return Resp()


def run_one(page, tmp_path, title="Markets Intern - Off-cycle 2027"):
    raws = [RawJob(title=title, url="https://bank.example/job/1", location="Paris, France")]

    class Adapter:
        @staticmethod
        def fetch(target, http):
            return raws

    cache = enrich.StartDateCache(tmp_path / "cache.json")
    run.get_adapter = lambda platform: Adapter
    kept, error, stat, _ = run.scrape_one(TARGET, Http({"https://bank.example/job/1": page}), cache)
    return kept, stat, cache


def test_ad_saying_april_removes_the_offer(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "get_adapter", run.get_adapter)
    kept, stat, _ = run_one(AD_APRIL, tmp_path)
    assert kept == [] and stat["removed_from_ad"] == 1


def test_ad_saying_june_dates_the_offer(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "get_adapter", run.get_adapter)
    kept, stat, _ = run_one(AD_JUNE, tmp_path)
    assert kept[0]["start"] == "2027-06" and stat["dated_from_ad"] == 1


def test_ad_without_explicit_start_keeps_the_offer(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "get_adapter", run.get_adapter)
    kept, stat, _ = run_one(AD_NOTHING, tmp_path)
    assert len(kept) == 1 and kept[0]["start"] == "2027"     # in doubt, kept


def test_json_ld_job_start_date(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "get_adapter", run.get_adapter)
    kept, stat, _ = run_one(AD_LD_START, tmp_path)
    assert kept[0]["start"] == "2027-09"


def test_unreadable_ad_keeps_the_offer_and_is_cached(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "get_adapter", run.get_adapter)

    class Broken:
        def get(self, url, **kwargs):
            raise OSError("down")
    cache = enrich.StartDateCache(tmp_path / "c.json")
    assert enrich.lookup("id1", "https://x.example/1", Broken(), cache, date(2026, 10, 24)) is None
    assert cache.get("id1")["error"] == "OSError"
    # not retried before a week
    assert enrich.lookup("id1", "https://x.example/1", Broken(), cache, date(2026, 10, 26)) is None
    assert cache.fetched == 1


def test_oracle_ads_are_read_through_the_api():
    seen = {}

    class Http:
        def get_json(self, url, **kwargs):
            seen["url"] = url
            return {"items": [{"ExternalDescriptionStr": "&lt;p&gt;Start date: September 2027&lt;/p&gt;"}]}

    text = enrich.read_ad("https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/210776890", Http())
    assert "recruitingCEJobRequisitionDetails" in seen["url"] and "210776890" in seen["url"] and "CX_1001" in seen["url"]
    assert text == "Start date: September 2027"


def test_workday_ads_are_read_through_the_api():
    seen = {}

    class Http:
        def get_json(self, url, **kwargs):
            seen["url"] = url
            return {"jobPostingInfo": {"jobDescription": "<p>Programme dates: start date: September 2027.</p>"}}

    text = enrich.read_ad("https://barclays.wd3.myworkdayjobs.com/External_Career_Site_Barclays/job/London/Off-Cycle_JR-1", Http())
    assert seen["url"] == "https://barclays.wd3.myworkdayjobs.com/wday/cxs/barclays/External_Career_Site_Barclays/job/London/Off-Cycle_JR-1"
    assert "September 2027" in text
