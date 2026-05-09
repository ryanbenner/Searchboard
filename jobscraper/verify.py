from __future__ import annotations
import asyncio
import httpx
from jobscraper.job import Job


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
}


async def _check(client: httpx.AsyncClient, sem: asyncio.Semaphore,
                 j: Job, timeout: float) -> bool:
    async with sem:
        try:
            r = await client.head(j.url, timeout=timeout, follow_redirects=True)
            if 200 <= r.status_code < 400:
                return True
            if r.status_code in (403, 405, 501):
                r = await client.get(j.url, timeout=timeout, follow_redirects=True)
                return 200 <= r.status_code < 400
            return False
        except (httpx.HTTPError, asyncio.TimeoutError):
            return False


async def _verify_all(jobs: list[Job], concurrency: int,
                      timeout: float) -> list[bool]:
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(headers=_HEADERS) as client:
        return await asyncio.gather(
            *[_check(client, sem, j, timeout) for j in jobs]
        )


def verify_links(jobs: list[Job], *, concurrency: int = 15,
                 timeout: float = 10.0) -> list[Job]:
    if not jobs:
        return []
    ok = asyncio.run(_verify_all(jobs, concurrency, timeout))
    return [j for j, alive in zip(jobs, ok) if alive]
