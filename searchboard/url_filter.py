from __future__ import annotations
import re
from urllib.parse import urlparse


_JOB_HOST_RE = re.compile(
    r"(^|\.)("
    r"greenhouse\.io|"
    r"lever\.co|"
    r"ashbyhq\.com|"
    r"workable\.com|"
    r"myworkdayjobs\.com|"
    r"bamboohr\.com|"
    r"rippling\.com|"
    r"breezy\.hr|"
    r"smartrecruiters\.com|"
    r"wellfound\.com|"
    r"workatastartup\.com|"
    r"jobvite\.com|"
    r"recruitee\.com|"
    r"teamtailor\.com|"
    r"recruiterbox\.com|"
    r"jobscore\.com"
    r")$"
)

_JOB_PATH_RE = re.compile(
    r"/(jobs?|careers?|positions?|opportunities|openings|join-us|"
    r"work-with-us|hiring|apply)(/|$|\?)",
    re.IGNORECASE,
)


def looks_like_job_url(url: str | None) -> bool:
    if not url:
        return False
    try:
        u = urlparse(url)
    except Exception:
        return False
    if not u.netloc:
        return False
    host = u.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if _JOB_HOST_RE.search(host):
        return True
    return bool(_JOB_PATH_RE.search(u.path or ""))
