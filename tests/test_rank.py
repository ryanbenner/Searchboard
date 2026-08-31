from datetime import date
from unittest.mock import MagicMock
from searchboard.config import load_profile
from searchboard.job import Job
from searchboard.rank import rank_jobs
from pathlib import Path


PROFILE = load_profile(Path(__file__).parent / "fixtures" / "profile_min.yml")


def _j(jid="x:y:1") -> Job:
    return Job(
        id=jid, source="x", company="X", title="Junior FS",
        location="Remote", remote=True, salary_min=80000, salary_max=120000,
        url="https://x", posted_at=None, seen_at=date.today(),
        description_text="Vue/Node",
    )


def test_rank_calls_claude_and_merges_scores():
    fake_client = MagicMock()
    fake_client.messages.create.return_value = MagicMock(
        content=[MagicMock(
            type="tool_use", name="submit_rankings",
            input={"rankings": [{"id": "x:y:1", "score": 88, "rationale": "Strong Vue/Node match"}]},
        )],
        usage=MagicMock(input_tokens=100, output_tokens=10,
                        cache_creation_input_tokens=0, cache_read_input_tokens=0),
    )
    out = rank_jobs([_j()], PROFILE, client=fake_client)
    assert out[0].score == 88
    assert out[0].rationale.startswith("Strong")

    args, kwargs = fake_client.messages.create.call_args
    assert kwargs["model"] == "claude-haiku-4-5"
    assert kwargs["tool_choice"] == {"type": "tool", "name": "submit_rankings"}
    sys = kwargs["system"]
    assert isinstance(sys, list) and sys[0]["cache_control"]["type"] == "ephemeral"
    assert "Test User" in sys[0]["text"]


def test_rank_handles_missing_id_gracefully():
    fake_client = MagicMock()
    fake_client.messages.create.return_value = MagicMock(
        content=[MagicMock(
            type="tool_use", name="submit_rankings",
            input={"rankings": []},
        )],
        usage=MagicMock(input_tokens=100, output_tokens=10,
                        cache_creation_input_tokens=0, cache_read_input_tokens=0),
    )
    out = rank_jobs([_j()], PROFILE, client=fake_client)
    assert out[0].score is None


def test_rank_reports_api_cost(capsys):
    fake_client = MagicMock()
    fake_client.messages.create.return_value = MagicMock(
        content=[MagicMock(
            type="tool_use", name="submit_rankings",
            input={"rankings": [{"id": "x:y:1", "score": 88, "rationale": "ok"}]},
        )],
        usage=MagicMock(input_tokens=200_000, output_tokens=10_000,
                        cache_creation_input_tokens=0, cache_read_input_tokens=0),
    )
    rank_jobs([_j()], PROFILE, client=fake_client)
    err = capsys.readouterr().err
    assert "rank_cost=$0.2500" in err
    assert "input_tokens=200000" in err
    assert "output_tokens=10000" in err
