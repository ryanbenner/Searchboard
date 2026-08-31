from datetime import date
from email.utils import parsedate_to_datetime
import hashlib
import re
import xml.etree.ElementTree as ET
import httpx
from searchboard.job import Job, make_id
from searchboard.sources import register
from searchboard.sources.base import Source

_HTML = re.compile(r"<[^>]+>")
_SALARY = re.compile(r"\$(\d{2,3}(?:,\d{3})?)\s*[–-]\s*\$(\d{2,3}(?:,\d{3})?)")


def _parse_salary(text: str) -> tuple[int | None, int | None]:
    m = _SALARY.search(text or "")
    if not m:
        return None, None
    return int(m.group(1).replace(",", "")), int(m.group(2).replace(",", ""))


def _company_from_link(link: str) -> str:
    tail = link.rsplit("/", 1)[-1]
    return tail.replace("-", " ").title()


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-") or "unknown"


@register("weworkremotely")
class WeWorkRemotely(Source):
    URL = "https://weworkremotely.com/categories/remote-{cat}-jobs.rss"

    def __init__(self, categories: list[str] | None = None, timeout: float = 20.0):
        self.categories = categories or [
            "programming", "full-stack-programming",
            "front-end-programming", "back-end-programming",
        ]
        self.timeout = timeout

    def fetch(self) -> list[Job]:
        out: list[Job] = []
        with httpx.Client(timeout=self.timeout) as c:
            for cat in self.categories:
                r = c.get(self.URL.format(cat=cat))
                if r.status_code != 200:
                    continue
                out.extend(self._parse_rss(r.text))
        return out

    def _parse_rss(self, xml: str) -> list[Job]:
        out: list[Job] = []
        root = ET.fromstring(xml)
        for item in root.iter("item"):
            link = (item.findtext("link") or "").strip()
            title = (item.findtext("title") or "").strip()
            desc_html = item.findtext("description") or ""
            desc = _HTML.sub(" ", desc_html)[:3000]
            posted = None
            if pd := item.findtext("pubDate"):
                try:
                    posted = parsedate_to_datetime(pd).date()
                except (TypeError, ValueError):
                    posted = None
            company = (item.findtext("company") or _company_from_link(link)).strip()
            slug = _slugify(company)
            posting_id = hashlib.sha1(link.encode()).hexdigest()[:12]
            lo, hi = _parse_salary(desc)
            out.append(Job(
                id=make_id("weworkremotely", slug, posting_id),
                source="weworkremotely",
                company=company,
                title=title,
                location=item.findtext("region") or "Remote",
                remote=True,
                salary_min=lo, salary_max=hi,
                url=link,
                posted_at=posted,
                seen_at=date.today(),
                description_text=desc,
            ))
        return out
