# Job Scout

Runs every morning, reads **public ATS job feeds** straight from company career sites
(no LinkedIn, no scraping), keeps only **early-career roles matching your target
positions**, appends them to a **Google Sheet**, and **emails you** a digest.

**➡ To set it up, follow `SETUP.md`.** This file explains the pieces.

## How it works
`fetch` (per-company ATS feed) → `normalize` → `match` (your role keywords) →
`early-career filter` → `dedupe` (against the Sheet) → `output` (Sheet + email).

## Files
```
job-scout/
├── config.yaml         # companies + role keywords + early-career rules + output  ← edit this
├── main.py             # orchestrator
├── matcher.py          # role-keyword matching + early-career / new-grad filter
├── gsheet.py           # Google Sheet append + dedup (source of truth for "seen")
├── notifier.py         # console + email digest (Gmail SMTP)
├── sources/
│   ├── greenhouse.py   # Waymo, SpaceX, Lucid, Anduril, Rocket Lab, Redwood, ...
│   ├── ashby.py        # Rivian-VW JV, Form Energy, Span, Base Power, ...
│   ├── lever.py        # Zoox, Waabi, Loft Orbital, Gravitics
│   ├── smartrecruiters.py  # Renesas, Bosch
│   └── workday.py      # Marvell, Blue Origin, Boeing, RTX, GE Vernova, Fluence, ...
├── requirements.txt
├── SETUP.md            # step-by-step: Sheet, Gmail app password, GitHub Actions
└── .github/workflows/scout.yml   # daily run on GitHub Actions (free)
```

## ~40 companies pre-loaded (big + small)
Automotive/AV: Rivian-VW JV, Waymo, Lucid, Aurora, Nuro, Scout, Harbinger, Zoox, Waabi, Aptiv.
Aerospace/defense: SpaceX, Archer, Anduril, Relativity, Rocket Lab, Stoke, Ursa Major,
Loft Orbital, Gravitics, Blue Origin, Sierra Space, Northrop, Boeing, RTX.
Semiconductor/power: Marvell, Renesas, Analog Devices, Wolfspeed, NXP.
Grid/energy/storage: GE Vernova, Fluence, Stem, Nextracker, Form Energy, Span, Base Power,
Redwood, ChargePoint, InCharge, Electric Hydrogen, Antora, Peak Energy, Group14, Sila,
Arc Boat, Astro Mechanica, Apex Space, GridCARE.

Companies with no clean public feed (Tesla, Joby, Lockheed, Enphase, TI, onsemi, etc.)
are listed but commented out in `config.yaml` — see SETUP.md.

## Add a company
Open any job posting on the company's site and read the URL to find its ATS, then add one
line under `companies:` in `config.yaml`:

| URL contains | `type` | identifier needed |
|---|---|---|
| `greenhouse.io/<x>` | `greenhouse` | token `<x>` |
| `jobs.lever.co/<x>` | `lever` | slug `<x>` |
| `jobs.ashbyhq.com/<x>` | `ashby` | token `<x>` (case-sensitive!) |
| `<x>.myworkdayjobs.com/...` | `workday` | host + tenant + site |
| `jobs.smartrecruiters.com/<x>` | `smartrecruiters` | company id `<x>` |
| `icims.com`, custom sites | — | no clean feed; use an aggregator |

## Local test
```bash
pip install -r requirements.txt
python main.py     # leave google_sheet_id blank in config to just print to console
```
