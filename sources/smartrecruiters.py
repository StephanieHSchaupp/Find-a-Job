"""SmartRecruiters public postings API. Used by Renesas, Bosch."""
import requests

API = "https://api.smartrecruiters.com/v1/companies/{company}/postings"


def fetch(company):
    cid = company["token"]
    out = []
    offset = 0
    while True:
        resp = requests.get(API.format(company=cid),
                            params={"limit": 100, "offset": offset}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("content", [])
        if not items:
            break
        for j in items:
            loc = j.get("location") or {}
            loc_str = ", ".join(x for x in [loc.get("city"), loc.get("region"),
                                            loc.get("country")] if x)
            out.append({
                "company": company["name"],
                "source": "smartrecruiters",
                "id": f"sr-{cid}-{j.get('id')}",
                "title": j.get("name", ""),
                "location": loc_str,
                "url": f"https://jobs.smartrecruiters.com/{cid}/{j.get('id')}",
                "posted_at": j.get("releasedDate", ""),
                "description": "",
            })
        offset += 100
        if offset >= data.get("totalFound", 0):
            break
    return out
