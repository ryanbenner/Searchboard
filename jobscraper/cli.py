from __future__ import annotations
import argparse
import os
import sys
from datetime import date
from pathlib import Path
from jobscraper.config import load_profile, load_companies, save_companies, Profile, Companies
from jobscraper.discover import discover_new_slugs, merge_into_companies
from jobscraper.digest import write_xlsx, render_markdown
from jobscraper.email import send_digest
from jobscraper.filter import hard_filter
from jobscraper.rank import rank_jobs
from jobscraper.verify import verify_links
from jobscraper.sources.greenhouse import Greenhouse
from jobscraper.sources.lever import Lever
from jobscraper.sources.ashby import Ashby
from jobscraper.sources.remoteok import RemoteOK
from jobscraper.sources.remotive import Remotive
from jobscraper.sources.weworkremotely import WeWorkRemotely
from jobscraper.sources.hn_whoshiring import HNWhosHiring
from jobscraper.store import Store


DATA_DIR = Path("data")
SCORE_FLOOR = 50
TOP_N = 100
DIGEST_LIMIT = 15


def _top(jobs):
    qualifying = [j for j in jobs if (j.score or 0) >= SCORE_FLOOR]
    qualifying.sort(key=lambda x: -(x.score or 0))
    return qualifying[:TOP_N]


def build_sources(profile: Profile, companies: Companies):
    return [
        Greenhouse(slugs=[e.slug for e in companies.greenhouse]),
        Lever(slugs=[e.slug for e in companies.lever]),
        Ashby(slugs=[e.slug for e in companies.ashby]),
        RemoteOK(),
        Remotive(),
        WeWorkRemotely(),
        HNWhosHiring(),
    ]


def cmd_run(_args) -> int:
    profile = load_profile("profile.yml")
    companies = load_companies("companies.yml")

    DATA_DIR.mkdir(exist_ok=True)
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

    ranked = rank_jobs(verified, profile)

    store = Store(DATA_DIR / "seen.sqlite")
    store.upsert(ranked, today=today)

    digest_jobs = store.unsent_top(today, score_floor=SCORE_FLOOR,
                                   limit=DIGEST_LIMIT)
    by_id = {j.id: j for j in ranked}
    # Hydrate digest jobs with full Job fields (location, rationale, etc.)
    # from the in-memory ranked list — store rows lack those.
    digest_full = [by_id[j.id] for j in digest_jobs if j.id in by_id]

    all_ranked_top = _top(ranked)
    still_open_full = [j for j in all_ranked_top
                       if j.id not in {d.id for d in digest_full}]
    print(f"ranked={len(ranked)} digest={len(digest_full)} "
          f"all_top={len(all_ranked_top)}", file=sys.stderr)

    snap = DATA_DIR / f"{today.isoformat()}.xlsx"
    write_xlsx(snap, new_today=digest_full, still_open=still_open_full,
               all_ranked=all_ranked_top)
    latest = DATA_DIR / "latest.xlsx"
    latest.write_bytes(snap.read_bytes())

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
        subject=f"JobScraper {today.isoformat()} — {len(digest_full)} new",
        markdown_body=md,
        xlsx_path=latest,
    )
    store.mark_sent([j.id for j in digest_full], today)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="jobscraper")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run", help="Run the daily pipeline.")
    args = p.parse_args(argv)
    if args.cmd == "run":
        return cmd_run(args)
    return 1
