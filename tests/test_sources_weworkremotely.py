from pathlib import Path
import respx, httpx
from jobscraper.sources.weworkremotely import WeWorkRemotely

FIX = Path(__file__).parent / "fixtures" / "wwr_programming.xml"


@respx.mock
def test_wwr_parses():
    respx.get("https://weworkremotely.com/categories/remote-programming-jobs.rss").mock(
        return_value=httpx.Response(200, text=FIX.read_text())
    )
    src = WeWorkRemotely(categories=["programming"])
    jobs = src.fetch()
    assert len(jobs) == 1
    j = jobs[0]
    assert j.source == "weworkremotely"
    assert j.remote is True
    assert "Junior Node" in j.title
    assert j.salary_min == 70000 and j.salary_max == 100000
