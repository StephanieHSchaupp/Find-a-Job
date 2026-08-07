"""Google Sheet output + dedup source of truth.

The Sheet is the single source of truth for "already seen" jobs: each run reads
the ID column, so you never get emailed the same role twice, even across machines.

Auth: set the env var GOOGLE_SERVICE_ACCOUNT_JSON to the full service-account
JSON (that's how GitHub Actions passes it), or drop a service_account.json file
next to this script for local runs. See SETUP.md.
"""
import json
import os
from datetime import date

# gspread / google-auth are imported lazily inside _client() so that console-only
# local runs (no google_sheet_id set) work with just requests + PyYAML installed.

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
HEADER = ["Date found", "Company", "Title", "Location", "Tier",
          "Roles", "Level note", "Status", "ID", "Link"]
ID_COL = 9  # column I, matches HEADER index of "ID"


def _client():
    import gspread
    from google.oauth2.service_account import Credentials
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if raw:
        creds = Credentials.from_service_account_info(json.loads(raw), scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
    return gspread.authorize(creds)


def _worksheet(sheet_id):
    ws = _client().open_by_key(sheet_id).sheet1
    # Make sure the header row exists
    if ws.acell("A1").value != HEADER[0]:
        ws.insert_row(HEADER, 1)
    return ws


def read_seen_ids(sheet_id):
    """Return the set of job IDs already in the Sheet."""
    ws = _worksheet(sheet_id)
    return set(ws.col_values(ID_COL)[1:])  # skip header


def append_matches(sheet_id, matches):
    """Append new matches as rows. 'Status' starts as 'New' for you to update."""
    if not matches:
        return
    ws = _worksheet(sheet_id)
    rows = [[
        date.today().isoformat(),
        m["job"]["company"],
        m["job"]["title"],
        m["job"]["location"],
        m["tier"],
        ", ".join(m["groups"]),
        m.get("note", ""),
        "New",
        m["job"]["id"],
        m["job"]["url"],
    ] for m in matches]
    ws.append_rows(rows, value_input_option="USER_ENTERED")
