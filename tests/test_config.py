from pathlib import Path
from jobscraper.config import load_profile, load_companies, save_companies, CompanyEntry


FIX = Path(__file__).parent / "fixtures"


def test_load_profile_min():
    p = load_profile(FIX / "profile_min.yml")
    assert p.email == "test@example.com"
    assert p.compensation.min_usd == 60000
    assert "secret clearance" in p.exclusions.keywords
    assert p.location.remote_ok is True


def test_load_companies_round_trip(tmp_path):
    c = load_companies(FIX / "companies_min.yml")
    assert len(c.greenhouse) == 1
    assert c.greenhouse[0].slug == "anthropic"
    assert c.disabled == []

    out = tmp_path / "out.yml"
    save_companies(c, out)
    c2 = load_companies(out)
    assert c2.greenhouse[0].slug == "anthropic"


def test_load_companies_dedups_on_save(tmp_path):
    c = load_companies(FIX / "companies_min.yml")
    c.greenhouse.append(CompanyEntry(slug="anthropic", discovered="2026-05-08", source="discovered"))
    out = tmp_path / "out.yml"
    save_companies(c, out)
    c2 = load_companies(out)
    assert len([e for e in c2.greenhouse if e.slug == "anthropic"]) == 1
