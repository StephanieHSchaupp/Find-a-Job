# Job Scout — Setup (daily, GitHub Actions + Google Sheet + email)

This runs the scout **once every morning** on GitHub's free servers, appends new
early-career matches to a **Google Sheet**, and **emails you** a digest. No computer
of yours needs to be on.

Three one-time setups: the Google Sheet, the Gmail app password, and the GitHub repo.
Budget ~30 minutes. Do them in order.

---

## Part 1 — Google Sheet + service account (so the script can write to it)

1. **Create the Sheet.** Make a new blank Google Sheet. From its URL grab the ID:
   `https://docs.google.com/spreadsheets/d/`**`THIS_LONG_ID`**`/edit`. Leave row 1 empty —
   the script writes the header automatically on first run.

2. **Create a Google Cloud project + service account** (free):
   - Go to <https://console.cloud.google.com/> → create a project (any name).
   - APIs & Services → **Enable APIs** → enable **Google Sheets API**.
   - APIs & Services → Credentials → **Create credentials → Service account**. Name it
     `job-scout`, click through, Done.
   - Open the service account → **Keys** tab → **Add key → Create new key → JSON**.
     A `.json` file downloads. Keep it safe — this is a secret.

3. **Share the Sheet with the service account.** Open the JSON file, copy the
   `client_email` value (looks like `job-scout@your-project.iam.gserviceaccount.com`).
   In your Google Sheet click **Share** and give that email **Editor** access.

4. **Put the Sheet ID in config.** In `config.yaml`, set:
   ```yaml
   output:
     google_sheet_id: "THIS_LONG_ID"
   ```

---

## Part 2 — Gmail app password (so the script can email you)

1. Your Google account needs **2-Step Verification** on (required for app passwords).
2. Go to <https://myaccount.google.com/apppasswords>, create one named `job-scout`,
   and copy the 16-character password.
3. In `config.yaml` set your addresses:
   ```yaml
   output:
     email_from: "youraddress@gmail.com"   # the Gmail the app password belongs to
     email_to:   "sschaupp@rivianvw.tech"  # where you want the digest (can be the same)
   ```
   (You don't put the app password in the file — it goes into GitHub secrets in Part 3.)

> Prefer not to use Gmail? Any SMTP works — swap the host/port in `notifier.py`.
> Or use a free transactional service (Resend, SendGrid) and adapt `send_email`.

---

## Part 3 — GitHub repo + secrets (so it runs daily on its own)

1. Create a **private** GitHub repo and upload this whole `job-scout` folder
   (including the `.github/workflows/scout.yml` file).
2. In the repo: **Settings → Secrets and variables → Actions → New repository secret**.
   Add two secrets:
   - `GOOGLE_SERVICE_ACCOUNT_JSON` → paste the **entire contents** of the JSON key file.
   - `GMAIL_APP_PASSWORD` → the 16-character app password from Part 2.
3. Go to the **Actions** tab, pick **Job Scout**, and click **Run workflow** to test it now.
   - First run: it will append every currently-open matching role to the Sheet and email
     you the list (could be a few dozen). That's expected — it's your starting backlog.
   - Every run after: you only get **new** postings, because the Sheet's ID column is the
     dedup memory.
4. It now runs automatically at the time in `scout.yml` (default 6:30am Pacific). Change
   the `cron` line to adjust.

---

## Try it locally first (optional but recommended)

```bash
pip install -r requirements.txt
# put the JSON key file next to the scripts as service_account.json, then:
python main.py
```
Or run with the Sheet ID blank in config to just print matches to the console — no
Google/email setup needed — so you can eyeball the filtering before going live.

---

## Tuning the results

- **Roles / keywords:** edit the `roles:` block in `config.yaml`.
- **Early-career strictness:** `early_career.strict: true` keeps only roles with a clear
  new-grad signal; `false` (default) also keeps unlabeled roles tagged "level unclear".
- **Experience ceiling:** `early_career.max_years_experience` (default 2).
- **Locations:** the `locations:` list; empty `[]` accepts anywhere.
- **Add a company:** find its ATS (see README) and add one line under `companies:`.

---

## Companies without a clean feed

Some targets run career sites with no public JSON feed and are intentionally left out of
`config.yaml` (they'd need custom scraping or a paid aggregator): **Tesla** (custom),
**Rivian main** and **Joby** (iCIMS), **Lockheed Martin** (Phenom), **Enphase /
Power Integrations / EVgo** (Jobvite), **Navitas** (Paycom), **Vicor / QuantumScape**
(SuccessFactors), **onsemi / TI / First Solar** (Oracle), **SolarEdge** (Comeet).
If you want any of these, the cleanest route is a jobs-aggregator API (Fantastic.jobs,
TheirStack, Coresignal) that already normalizes them — add an `aggregator` source module.

## Notes / gotchas
- Several aerospace/defense roles (SpaceX, Anduril, Relativity, Rocket Lab, Stoke, Blue
  Origin, Sierra Space, Northrop, Boeing, RTX) are **ITAR / US-person-only**, and the
  primes often also require an active security clearance. The alert still fires; just
  expect that eligibility screen.
- **Workday** feeds were verified by careers URL but the POST endpoint wasn't exercised
  end-to-end — if one returns nothing, open that company's careers page and re-check the
  `host / tenant / site` values against the live URL.
- Be polite: this runs once a day, which no feed will mind.
