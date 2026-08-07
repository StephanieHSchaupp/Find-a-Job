"""Ashby public job posting API. Used by the Rivian-VW JV, Form Energy, Span, etc."""
import requests

API = "https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true"


def fetch(company):
    token = company["token"]
    resp = requests.get(API.format(token=token), timeout=30)
    resp.raise_for_status()
    postings = resp.json().get("jobs", [])
    out = []
    for j in postings:
        out.append({
            "company": company["name"],
            "source": "ashby",
            "id": f"ashby-{token}-{j.get('id')}",
            "title": j.get("title", ""),
            "location": j.get("location", ""),
            "url": j.get("jobUrl", ""),
            "posted_at": j.get("publishedAt", ""),
            "description": j.get("descriptionPlain", ""),
        })
    return out
