import json
from pathlib import Path
import respx, httpx
from searchboard.sources.greenhouse import Greenhouse


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


@respx.mock
def test_greenhouse_handles_null_location_name():
    payload = {
        "jobs": [{
            "id": 123,
            "title": "Engineer",
            "absolute_url": "https://boards.greenhouse.io/acme/jobs/123",
            "location": {"name": None},
            "content": "",
            "metadata": [],
            "updated_at": "2026-05-01T00:00:00Z",
        }]
    }
    respx.get("https://boards-api.greenhouse.io/v1/boards/acme/jobs").mock(
        return_value=httpx.Response(200, json=payload)
    )
    src = Greenhouse(slugs=["acme"])
    jobs = src.fetch()
    assert len(jobs) == 1
    assert jobs[0].location == ""
    assert jobs[0].remote is False
