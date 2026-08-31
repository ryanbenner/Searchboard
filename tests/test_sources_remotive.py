import json, respx, httpx
from pathlib import Path
from searchboard.sources.remotive import Remotive

FIX = Path(__file__).parent / "fixtures" / "remotive.json"

@respx.mock
def test_remotive_parses():
    respx.get("https://remotive.com/api/remote-jobs").mock(
        return_value=httpx.Response(200, json=json.loads(FIX.read_text()))
    )
    jobs = Remotive().fetch()
    assert len(jobs) == 1
    j = jobs[0]
    assert j.source == "remotive"
    assert j.id == "remotive:beta-co:1234567"
    assert j.salary_min == 60000 and j.salary_max == 90000
    assert j.remote is True
