import json, respx, httpx
from pathlib import Path
from jobscraper.sources.hn_whoshiring import HNWhosHiring

FIX = Path(__file__).parent / "fixtures"


@respx.mock
def test_hn_picks_latest_thread_and_parses_comments():
    respx.get("https://hn.algolia.com/api/v1/search").mock(
        return_value=httpx.Response(200, json=json.loads((FIX/"hn_search.json").read_text()))
    )
    respx.get("https://hn.algolia.com/api/v1/items/40000000").mock(
        return_value=httpx.Response(200, json=json.loads((FIX/"hn_thread.json").read_text()))
    )
    jobs = HNWhosHiring().fetch()
    assert len(jobs) == 1
    j = jobs[0]
    assert j.source == "hn"
    assert j.id == "hn:hn:40000001"
    assert j.company.lower().startswith("delta")
    assert j.remote is True


@respx.mock
def test_hn_filters_out_homepage_only_urls():
    respx.get("https://hn.algolia.com/api/v1/search").mock(
        return_value=httpx.Response(200, json={"hits": [
            {"objectID": "1", "title": "Ask HN: Who is hiring? (May 2026)"}
        ]})
    )
    respx.get("https://hn.algolia.com/api/v1/items/1").mock(
        return_value=httpx.Response(200, json={
            "id": 1,
            "children": [
                {"id": 100, "created_at_i": 1746140000,
                 "text": "Cortico | Full Stack Engineer | Remote (US) | Apply: https://cortico.ai"},
                {"id": 101, "created_at_i": 1746140100,
                 "text": "Acme | SWE | Remote (US) | Apply: https://jobs.lever.co/acme/xyz"},
            ],
        })
    )
    jobs = HNWhosHiring().fetch()
    assert [j.id for j in jobs] == ["hn:hn:101"]
