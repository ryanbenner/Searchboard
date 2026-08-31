from searchboard.url_filter import looks_like_job_url


def test_greenhouse_host_passes():
    assert looks_like_job_url("https://boards.greenhouse.io/notion/jobs/123")


def test_lever_host_passes():
    assert looks_like_job_url("https://jobs.lever.co/notion/abc-def")


def test_ashby_host_passes():
    assert looks_like_job_url("https://jobs.ashbyhq.com/replit/uuid-here")


def test_workable_host_passes():
    assert looks_like_job_url("https://apply.workable.com/acme/j/ABC123")


def test_workatastartup_passes():
    assert looks_like_job_url("https://www.workatastartup.com/jobs/12345")


def test_custom_careers_path_passes():
    assert looks_like_job_url("https://example.com/careers/swe-2026")


def test_jobs_path_passes():
    assert looks_like_job_url("https://acme.com/jobs/123")


def test_apply_path_passes():
    assert looks_like_job_url("https://acme.com/apply/role-x")


def test_bare_homepage_fails():
    assert not looks_like_job_url("https://cortico.ai")


def test_homepage_trailing_slash_fails():
    assert not looks_like_job_url("https://metabase.com/")


def test_unrelated_blog_fails():
    assert not looks_like_job_url(
        "https://blog.expensify.com/2016/06/03/rule-1-get-shit-done/"
    )


def test_event_platform_fails():
    assert not looks_like_job_url("https://jam.awsevents.com")


def test_company_root_fails():
    assert not looks_like_job_url("https://greenstork.com")


def test_empty_string_fails():
    assert not looks_like_job_url("")


def test_none_fails():
    assert not looks_like_job_url(None)


def test_garbled_fails():
    assert not looks_like_job_url("not a url at all")
