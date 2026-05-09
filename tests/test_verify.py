from datetime import date
import httpx
import respx
from jobscraper.job import Job
from jobscraper.verify import verify_links


def _j(jid, url):
    return Job(
        id=jid, source="x", company="X", title="Software Engineer",
        location="Remote", remote=True, salary_min=None, salary_max=None,
        url=url, posted_at=None, seen_at=date.today(), description_text="",
    )


@respx.mock
def test_keeps_live_urls():
    respx.head("https://example.com/live").mock(return_value=httpx.Response(200))
    jobs = [_j("a:1", "https://example.com/live")]
    assert len(verify_links(jobs)) == 1


@respx.mock
def test_drops_404_urls():
    respx.head("https://example.com/dead").mock(return_value=httpx.Response(404))
    jobs = [_j("a:2", "https://example.com/dead")]
    assert verify_links(jobs) == []


@respx.mock
def test_falls_back_to_get_on_405():
    respx.head("https://example.com/no-head").mock(return_value=httpx.Response(405))
    respx.get("https://example.com/no-head").mock(return_value=httpx.Response(200))
    jobs = [_j("a:3", "https://example.com/no-head")]
    assert len(verify_links(jobs)) == 1


@respx.mock
def test_drops_on_network_error():
    respx.head("https://example.com/err").mock(side_effect=httpx.ConnectError("boom"))
    jobs = [_j("a:4", "https://example.com/err")]
    assert verify_links(jobs) == []


@respx.mock
def test_mixed_batch():
    respx.head("https://example.com/a").mock(return_value=httpx.Response(200))
    respx.head("https://example.com/b").mock(return_value=httpx.Response(404))
    respx.head("https://example.com/c").mock(return_value=httpx.Response(301,
        headers={"location": "https://example.com/c-final"}))
    respx.head("https://example.com/c-final").mock(return_value=httpx.Response(200))
    jobs = [
        _j("x:a", "https://example.com/a"),
        _j("x:b", "https://example.com/b"),
        _j("x:c", "https://example.com/c"),
    ]
    out = verify_links(jobs)
    assert {j.id for j in out} == {"x:a", "x:c"}


def test_empty_input():
    assert verify_links([]) == []
