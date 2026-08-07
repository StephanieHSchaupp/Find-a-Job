"""Output stage: Google Sheet + email. Both are STUBS with clear TODOs.

Start by just using `print_matches` (console) to validate the pipeline, then
wire up the sheet and email once matches look right.
"""
import smtplib
import ssl
from email.message import EmailMessage


def print_matches(matches):
    """Console output — use this first to validate everything works."""
    if not matches:
        print("No new matches this run.")
        return
    print(f"\n=== {len(matches)} new matching job(s) ===")
    for m in matches:
        job, tier, groups = m["job"], m["tier"], m["groups"]
        print(f"[{tier.upper():8}] {job['company']:14} | {job['title']}")
        print(f"           {job['location']}  ({', '.join(groups)})")
        print(f"           {m.get('note', '')}")
        print(f"           {job['url']}\n")


# ---------------------------------------------------------------------------
# Email output (Gmail SMTP + app password)
# ---------------------------------------------------------------------------
def send_email(matches, cfg, gmail_app_password=None):
    """Send a digest via Gmail SMTP. Needs env var GMAIL_APP_PASSWORD
    (create one at myaccount.google.com/apppasswords) and email_from set in config.
    """
    to = cfg["output"]["email_to"]
    frm = cfg["output"]["email_from"]
    if not matches:
        print("[email] no new matches, nothing to send")
        return
    if not (to and frm and gmail_app_password):
        print(f"[email] skipped (email_from/to set: {bool(to and frm)}, "
              f"password set: {bool(gmail_app_password)})")
        return

    strong = [m for m in matches if m["tier"] == "strong"]
    lines = [f"{len(matches)} new early-career match(es) "
             f"({len(strong)} strong). Newest roles across your target companies:\n"]
    for m in matches:
        j = m["job"]
        lines.append(f"[{m['tier'].upper()}] {j['company']} — {j['title']}")
        lines.append(f"  {j['location']}  ({', '.join(m['groups'])})  |  {m.get('note','')}")
        lines.append(f"  {j['url']}\n")
    body = "\n".join(lines)

    msg = EmailMessage()
    msg["Subject"] = f"Job Scout: {len(matches)} new early-career match(es)"
    msg["From"] = frm
    msg["To"] = to
    msg.set_content(body)

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
        server.login(frm, gmail_app_password)
        server.send_message(msg)
    print(f"[email] sent {len(matches)} match(es) to {to}")
