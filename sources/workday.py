"""Workday CxS job search endpoint. Used by Marvell, Boeing, RTX, GE Vernova, etc."""
import requests

HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}


def fetch(company):
    host = company["host"]
    tenant = company["tenant"]
    site = company["site"]
    url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
    out = []
    offset = 0
    while True:
        body = {"limit": 20, "offset": offset, "searchText": "", "appliedFacets": {}}
        resp = requests.post(url, json=body, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        postings = data.get("jobPostings", [])
        if not postings:
            break
        for j in postings:
            path = j.get("externalPath", "")
            out.append({
                "company": company["name"],
                "source": "workday",
                "id": f"wd-{tenant}-{path}",
                "title": j.get("title", ""),
                "location": j.get("locationsText", ""),
                "url": f"https://{host}/en-US/{site}{path}",
                "posted_at": j.get("postedOn", ""),
                "description": "",
            })
        offset += 20
        if offset >= data.get("total", 0):
            break
    return out
