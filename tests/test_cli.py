import shutil
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock
from openpyxl import load_workbook
from jobscraper import cli
from jobscraper.job import Job


def _j(jid, title="Junior Software Engineer", score=None):
    return Job(
        id=jid, source=jid.split(":")[0], company="ACo", title=title,
        location="Remote", remote=True, salary_min=80000, salary_max=120000,
        url="https://x", posted_at=None, seen_at=date.today(),
        description_text="vue/node", score=score, rationale=None,
    )


def test_cli_run_end_to_end(tmp_path, monkeypatch):
    shutil.copy(Path(__file__).parent / "fixtures" / "profile_min.yml", tmp_path / "profile.yml")
    shutil.copy(Path(__file__).parent / "fixtures" / "companies_min.yml", tmp_path / "companies.yml")
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()

    fake_src = MagicMock()
    fake_src.fetch.return_value = [_j("greenhouse:anthropic:1")]
    monkeypatch.setattr(cli, "build_sources",
                        lambda profile, companies: [fake_src])
    monkeypatch.setattr(cli, "verify_links", lambda jobs, **kw: jobs)

    def fake_rank(jobs, profile, client=None):
        for j in jobs: j.score = 90; j.rationale = "great match"
        return jobs
    monkeypatch.setattr(cli, "rank_jobs", fake_rank)

    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "u@example.com")
    monkeypatch.setenv("SMTP_PASS", "p")
    monkeypatch.setenv("EMAIL_TO", "u@example.com")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")

    sent = {}
    def fake_send(**kw): sent.update(kw)
    monkeypatch.setattr(cli, "send_digest", fake_send)

    cli.main(["run"])

    xlsx = tmp_path / "data" / "latest.xlsx"
    assert xlsx.exists()
    wb = load_workbook(xlsx)
    assert wb["New today"].cell(2, 1).value == 90
    assert sent["to"] == "u@example.com"
    assert "great match" in sent["markdown_body"]

    # Second run with the same job should NOT re-email — sent queue drained.
    sent.clear()
    cli.main(["run"])
    assert sent == {}, "second run must not email already-sent jobs"


def test_cli_skips_email_when_no_unsent_jobs(tmp_path, monkeypatch):
    shutil.copy(Path(__file__).parent / "fixtures" / "profile_min.yml", tmp_path / "profile.yml")
    shutil.copy(Path(__file__).parent / "fixtures" / "companies_min.yml", tmp_path / "companies.yml")
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()

    fake_src = MagicMock()
    fake_src.fetch.return_value = [_j("greenhouse:anthropic:1")]
    monkeypatch.setattr(cli, "build_sources",
                        lambda profile, companies: [fake_src])
    monkeypatch.setattr(cli, "verify_links", lambda jobs, **kw: jobs)
    # Score below floor → not eligible
    monkeypatch.setattr(cli, "rank_jobs",
                        lambda jobs, profile, client=None: [
                            setattr(j, "score", 30) or j for j in jobs
                        ])

    for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "EMAIL_TO", "ANTHROPIC_API_KEY"):
        monkeypatch.setenv(k, "x")
    monkeypatch.setenv("SMTP_PORT", "587")

    called = []
    monkeypatch.setattr(cli, "send_digest", lambda **kw: called.append(kw))

    cli.main(["run"])
    assert called == [], "should not send email when no eligible jobs"
