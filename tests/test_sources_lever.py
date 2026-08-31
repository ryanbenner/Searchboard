import json
from pathlib import Path
import respx, httpx
from searchboard.sources.lever import Lever


FIX = Path(__file__).parent / "fixtures" / "lever_notion.json"


@respx.mock
def test_lever_parses_jobs():
    respx.get("https://api.lever.co/v0/postings/notion").mock(
        return_value=httpx.Response(200, json=json.loads(FIX.read_text()))
    )
    src = Lever(slugs=["notion"])
    jobs = src.fetch()
    assert len(jobs) == 1
    j = jobs[0]
    assert j.source == "lever"
    assert j.id == "lever:notion:abc-123"
    assert j.remote is True
    assert j.salary_min == 150000 and j.salary_max == 200000
