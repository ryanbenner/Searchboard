import json
from pathlib import Path
import respx, httpx
from jobscraper.sources.greenhouse import Greenhouse


FIX = Path(__file__).parent / "fixtures" / "greenhouse_anthropic.json"


@respx.mock
def test_greenhouse_parses_jobs():
    respx.get("https://boards-api.greenhouse.io/v1/boards/anthropic/jobs").mock(
        return_value=httpx.Response(200, json=json.loads(FIX.read_text()))
    )
    src = Greenhouse(slugs=["anthropic"])
    jobs = src.fetch()
    assert len(jobs) >= 1
    j = jobs[0]
    assert j.source == "greenhouse"
    assert j.company == "Anthropic"
    assert j.id.startswith("greenhouse:anthropic:")
    assert j.url.startswith("https://boards.greenhouse.io/anthropic/jobs/")
    assert "<p>" not in j.description_text


@respx.mock
def test_greenhouse_skips_404_slugs():
    respx.get("https://boards-api.greenhouse.io/v1/boards/missing/jobs").mock(
        return_value=httpx.Response(404)
    )
    src = Greenhouse(slugs=["missing"])
    assert src.fetch() == []
    assert src.failed_slugs == ["missing"]
