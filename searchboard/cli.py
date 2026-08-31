from __future__ import annotations
import argparse
import hashlib
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from searchboard.config import load_profile, load_companies, save_companies, Profile, Companies
from searchboard.discover import discover_new_slugs, merge_into_companies
from searchboard.digest import write_xlsx, render_markdown
from searchboard.email import send_digest
from searchboard.filter import hard_filter
from searchboard.rank import rank_jobs
from searchboard.verify import verify_links
from searchboard.sources.greenhouse import Greenhouse
from searchboard.sources.lever import Lever
from searchboard.sources.ashby import Ashby
from searchboard.sources.smartrecruiters import SmartRecruiters
from searchboard.sources.remoteok import RemoteOK
from searchboard.sources.remotive import Remotive
from searchboard.sources.weworkremotely import WeWorkRemotely
from searchboard.sources.hn_whoshiring import HNWhosHiring
from searchboard.store import Store


SCORE_FLOOR = 50
TOP_N = 100
DIGEST_LIMIT = 15
MAX_AGE_DAYS = 21


def _fresh(jobs, today: date):
    cutoff = today - timedelta(days=MAX_AGE_DAYS)
    return [j for j in jobs if j.posted_at is None or j.posted_at >= cutoff]


def _top(jobs):
    qualifying = [j for j in jobs if (j.score or 0) >= SCORE_FLOOR]
    qualifying.sort(key=lambda x: -(x.score or 0))
    return qualifying[:TOP_N]


def build_sources(profile: Profile, companies: Companies):
    return [
        Greenhouse(slugs=[e.slug for e in companies.greenhouse]),
        Lever(slugs=[e.slug for e in companies.lever]),
        Ashby(slugs=[e.slug for e in companies.ashby]),
        SmartRecruiters(slugs=[e.slug for e in companies.smartrecruiters]),
        RemoteOK(),
        Remotive(),
        WeWorkRemotely(),
        HNWhosHiring(),
    ]


def cmd_run(args) -> int:
    profile = load_profile(args.profile)
    companies = load_companies("companies.yml")

    data_dir = Path(args.data_dir)
    data_dir.mkdir(exist_ok=True)
    today = date.today()

    raw: list = []
    for src in build_sources(profile, companies):
        try:
            raw.extend(src.fetch())
        except Exception as e:
            print(f"[warn] {src.__class__.__name__} failed: {e}", file=sys.stderr)

    new = discover_new_slugs(raw, companies)
    if new:
        merge_into_companies(companies, new, source_label="discovered")
        save_companies(companies, "companies.yml")

    filtered = hard_filter(raw, profile)
    print(f"raw={len(raw)} filtered={len(filtered)}", file=sys.stderr)

    verified = verify_links(filtered)
    print(f"verified={len(verified)} (dropped {len(filtered) - len(verified)} dead links)",
          file=sys.stderr)

    store = Store(data_dir / "seen.sqlite")

    # only send unscored jobs to the API; a profile edit re-ranks everything
    profile_hash = hashlib.sha256(Path(args.profile).read_bytes()).hexdigest()
    known = {} if store.get_meta("profile_hash") != profile_hash else store.scores()
    to_rank = [j for j in verified if j.id not in known]
    rank_jobs(to_rank, profile)
    for j in verified:
        if j.id in known:
            j.score, j.rationale = known[j.id]
    store.set_meta("profile_hash", profile_hash)
    ranked = verified
    print(f"scored_new={len(to_rank)} reused={len(verified) - len(to_rank)}",
          file=sys.stderr)

    store.upsert(ranked, today=today)

    digest_jobs = store.unsent_top(today, score_floor=SCORE_FLOOR,
                                   limit=DIGEST_LIMIT, max_age_days=MAX_AGE_DAYS)
    by_id = {j.id: j for j in ranked}
    # Hydrate digest jobs with full Job fields (location, rationale, etc.)
    # from the in-memory ranked list — store rows lack those.
    digest_full = [by_id[j.id] for j in digest_jobs if j.id in by_id]

    all_ranked_top = _top(_fresh(ranked, today))
    still_open_full = [j for j in all_ranked_top
                       if j.id not in {d.id for d in digest_full}]
    print(f"ranked={len(ranked)} digest={len(digest_full)} "
          f"all_top={len(all_ranked_top)}", file=sys.stderr)

    snap = data_dir / f"{today.isoformat()}.xlsx"
    write_xlsx(snap, new_today=digest_full, still_open=still_open_full,
               all_ranked=all_ranked_top)
    latest = data_dir / "latest.xlsx"
    latest.write_bytes(snap.read_bytes())

    if args.no_email:
        print("--no-email: skipping digest email", file=sys.stderr)
        return 0

    if not digest_full:
        print("no unsent jobs above floor; skipping email", file=sys.stderr)
        return 0

    md = render_markdown(digest_full, top_n=DIGEST_LIMIT)
    send_digest(
        host=os.environ["SMTP_HOST"],
        port=int(os.environ["SMTP_PORT"]),
        user=os.environ["SMTP_USER"],
        password=os.environ["SMTP_PASS"],
        to=os.environ["EMAIL_TO"],
        subject=f"Searchboard {today.isoformat()} — {len(digest_full)} new",
        markdown_body=md,
        xlsx_path=latest,
    )
    store.mark_sent([j.id for j in digest_full], today)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="searchboard")
    sub = p.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="Run the daily pipeline.")
    run.add_argument("--no-email", action="store_true",
                     help="Skip digest email and mark_sent.")
    run.add_argument("--profile", default="profile.yml",
                     help="Path to profile.yml.")
    run.add_argument("--data-dir", default="data",
                     help="Directory for seen.sqlite and xlsx output.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "run":
        return cmd_run(args)
    return 1
