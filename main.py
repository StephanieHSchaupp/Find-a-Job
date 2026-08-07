"""Job Scout — entry point.

Pipeline:  fetch -> normalize (done in sources) -> match -> dedupe -> output.

Run locally:
    pip install -r requirements.txt
    python main.py

The `seen.json` file remembers which jobs you've already been alerted about,
so you only ever get notified once per posting.
"""
import json
import os
import sys
from pathlib import Path

import yaml

from sources import FETCHERS
from matcher import match
import notifier
import gsheet

HERE = Path(__file__).parent
SEEN_FILE = HERE / "seen.json"


def load_config():
    with open(HERE / "config.yaml") as f:
        return yaml.safe_load(f)


def load_seen():
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text()))
    return set()


def save_seen(seen):
    SEEN_FILE.write_text(json.dumps(sorted(seen), indent=2))


def run():
    cfg = load_config()
    sheet_id = cfg["output"].get("google_sheet_id")

    # The Google Sheet is the source of truth for "already seen" jobs.
    # Fall back to a local seen.json only when no sheet is configured (local testing).
    if sheet_id:
        seen = gsheet.read_seen_ids(sheet_id)
        print(f"[seen] {len(seen)} job(s) already in the Sheet")
    else:
        seen = load_seen()

    new_matches = []

    for company in cfg["companies"]:
        fetcher = FETCHERS.get(company["type"])
        if not fetcher:
            print(f"[skip] {company['name']}: no fetcher for type '{company['type']}'")
            continue
        try:
            jobs = fetcher(company)
        except Exception as e:  # keep going if one source is down
            print(f"[error] {company['name']}: {e}")
            continue
        print(f"[ok] {company['name']}: {len(jobs)} jobs fetched")

        for job in jobs:
            if job["id"] in seen:
                continue
            tier, groups, note = match(job, cfg)
            if tier:
                new_matches.append({
                    "job": job, "tier": tier, "groups": groups, "note": note,
                })
            seen.add(job["id"])  # mark seen whether or not it matched

    # sort strong matches first
    new_matches.sort(key=lambda m: 0 if m["tier"] == "strong" else 1)

    # --- output ---
    notifier.print_matches(new_matches)
    if sheet_id:
        gsheet.append_matches(sheet_id, new_matches)
        print(f"[sheet] appended {len(new_matches)} row(s)")
    else:
        save_seen(seen)  # local-only dedup store
    notifier.send_email(new_matches, cfg, os.environ.get("GMAIL_APP_PASSWORD"))

    return len(new_matches)


if __name__ == "__main__":
    count = run()
    print(f"\nDone. {count} new match(es).")
    sys.exit(0)
