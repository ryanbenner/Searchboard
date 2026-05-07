import json
from pathlib import Path
import respx, httpx
from jobscraper.sources.remoteok import RemoteOK


FIX = Path(__file__).parent / "fixtures" / "remoteok.json"


@respx.mock
def test_remoteok_skips_metadata_and_parses():
    respx.get("https://remoteok.com/api").mock(
        return_value=httpx.Response(200, json=json.loads(FIX.read_text()))
    )
    jobs = RemoteOK().fetch()
    assert len(jobs) == 1
    j = jobs[0]
    assert j.source == "remoteok"
    assert j.id == "remoteok:acme:98765"
    assert j.remote is True
    assert j.salary_min == 80000
