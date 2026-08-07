"""Lever public postings API. Used by Zoox, Waabi, Loft Orbital, Gravitics."""
import requests

API = "https://api.lever.co/v0/postings/{slug}?mode=json"


def fetch(company):
    slug = company["token"]
    resp = requests.get(API.format(slug=slug), timeout=30)
    resp.raise_for_status()
    postings = resp.json()
    out = []
    for j in postings:
        cats = j.get("categories") or {}
        out.append({
            "company": company["name"],
            "source": "lever",
            "id": f"lever-{slug}-{j.get('id')}",
            "title": j.get("text", ""),
            "location": cats.get("location", ""),
            "url": j.get("hostedUrl", ""),
            "posted_at": j.get("createdAt", ""),
            "description": j.get("descriptionPlain", ""),
        })
    return out
