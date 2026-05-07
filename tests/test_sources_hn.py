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
