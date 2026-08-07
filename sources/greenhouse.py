"""Greenhouse public job board API. Used by Waymo, SpaceX, and many others."""
import requests

API = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"


def fetch(company):
    token = company["token"]
    resp = requests.get(API.format(token=token), timeout=30)
    resp.raise_for_status()
    jobs = resp.json().get("jobs", [])
    out = []
    for j in jobs:
        out.append({
            "company": company["name"],
            "source": "greenhouse",
            "id": f"gh-{token}-{j['id']}",
            "title": j.get("title", ""),
            "location": (j.get("location") or {}).get("name", ""),
            "url": j.get("absolute_url", ""),
            "posted_at": j.get("updated_at", ""),
            "description": j.get("content", ""),
        })
    return out
