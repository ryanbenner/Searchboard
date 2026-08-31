from datetime import date
from searchboard.sources.base import Source
from searchboard.sources import REGISTRY, register
from searchboard.job import Job


@register("dummy")
class _Dummy(Source):
    name = "dummy"

    def fetch(self) -> list[Job]:
        return [Job(
            id="dummy:x:1", source="dummy", company="X", title="T",
            location="Remote", remote=True, salary_min=None, salary_max=None,
            url="https://x", posted_at=None, seen_at=date.today(),
            description_text="",
        )]


def test_registry_has_dummy():
    assert "dummy" in REGISTRY
    assert REGISTRY["dummy"] is _Dummy


def test_dummy_fetch_returns_jobs():
    s = _Dummy()
    jobs = s.fetch()
    assert len(jobs) == 1
    assert jobs[0].source == "dummy"
