import json
from pathlib import Path
import respx, httpx
from jobscraper.sources.smartrecruiters import SmartRecruiters


FIX = Path(__file__).parent / "fixtures"


def _route(slug: str, offset: int, body: dict):
    return respx.get(
        f"https://api.smartrecruiters.com/v1/companies/{slug}/postings",
        params={"limit": 100, "offset": offset},
    ).mock(return_value=httpx.Response(200, json=body))


@respx.mock
def test_smartrecruiters_parses_jobs():
    body = json.loads((FIX / "smartrecruiters_visa_page1.json").read_text())
    body["totalFound"] = 2  # fit in one page for this test
    body["content"] = body["content"][:2]
    respx.get(
        "https://api.smartrecruiters.com/v1/companies/Visa/postings"
    ).mock(return_value=httpx.Response(200, json=body))
    src = SmartRecruiters(slugs=["Visa"])
    jobs = src.fetch()
    assert len(jobs) == 2
    j = jobs[0]
    assert j.source == "smartrecruiters"
    assert j.company == "Visa"
    assert j.title == "Sr. SW Engineer"
    assert j.location == "Austin, TX, United States"
    assert j.id == "smartrecruiters:visa:744000122509268"
    assert j.url == "https://jobs.smartrecruiters.com/Visa/744000122509268"
    assert j.remote is False
    # Second job is remote
    assert jobs[1].remote is True


@respx.mock
def test_smartrecruiters_paginates():
    p1 = json.loads((FIX / "smartrecruiters_visa_page1.json").read_text())
    p2 = json.loads((FIX / "smartrecruiters_visa_page2.json").read_text())
    respx.get(
        "https://api.smartrecruiters.com/v1/companies/Visa/postings"
    ).mock(side_effect=[
        httpx.Response(200, json=p1),
        httpx.Response(200, json=p2),
    ])
    src = SmartRecruiters(slugs=["Visa"])
    jobs = src.fetch()
    assert len(jobs) == 3
    titles = [j.title for j in jobs]
    assert "Senior Product Designer" in titles


@respx.mock
def test_smartrecruiters_empty_slug_yields_nothing():
    respx.get(
        "https://api.smartrecruiters.com/v1/companies/Nobody/postings"
    ).mock(return_value=httpx.Response(
        200, json={"offset": 0, "limit": 100, "totalFound": 0, "content": []}))
    src = SmartRecruiters(slugs=["Nobody"])
    assert src.fetch() == []


@respx.mock
def test_smartrecruiters_handles_missing_location_fields():
    body = {
        "offset": 0, "limit": 100, "totalFound": 1,
        "content": [{
            "id": "1",
            "name": "Engineer",
            "company": {"identifier": "Acme", "name": "Acme"},
            "releasedDate": "2026-05-01T00:00:00.000Z",
            "location": {},  # no fullLocation, no remote
        }],
    }
    respx.get(
        "https://api.smartrecruiters.com/v1/companies/Acme/postings"
    ).mock(return_value=httpx.Response(200, json=body))
    src = SmartRecruiters(slugs=["Acme"])
    jobs = src.fetch()
    assert len(jobs) == 1
    assert jobs[0].location == ""
    assert jobs[0].remote is False
