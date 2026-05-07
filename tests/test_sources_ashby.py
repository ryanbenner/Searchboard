import json
from pathlib import Path
import respx, httpx
from jobscraper.sources.ashby import Ashby


FIX = Path(__file__).parent / "fixtures" / "ashby_linear.json"


@respx.mock
def test_ashby_parses():
    respx.get("https://api.ashbyhq.com/posting-api/job-board/linear").mock(
        return_value=httpx.Response(200, json=json.loads(FIX.read_text()))
    )
    src = Ashby(slugs=["linear"])
    jobs = src.fetch()
    assert len(jobs) == 1
    assert jobs[0].id == "ashby:linear:job_01HX"
    assert jobs[0].remote is True
    assert jobs[0].salary_min == 160000
