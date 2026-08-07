"""Decide whether a job matches your target roles AND is early-career."""
import re

TAG_RE = re.compile(r"<[^>]+>")
# "5+ years", "3-5 years", "minimum of 4 years", "at least 6 years"
YEARS_RE = re.compile(r"(\d+)\s*\+?\s*(?:to|-|–)?\s*\d*\s*years?", re.I)
# whole-word mid/senior level tokens (avoids matching "Hawaii", "review", etc.)
LEVEL_RE = re.compile(r"\b(ii|iii|iv|v)\b", re.I)


def _clean(text):
    return TAG_RE.sub(" ", text or "").lower()


def is_early_career(job, ec):
    """Return (keep: bool, note: str). `ec` is the early_career config block."""
    title = _clean(job.get("title"))
    desc = _clean(job.get("description"))
    text = f"{title} {desc}"

    # 1. Hard senior/mid exclusions in the title
    for bad in ec.get("seniority_exclusions", []):
        if bad.lower() in title:
            return False, f"excluded: title contains '{bad}'"

    # 2. Mid-level roman numerals in the title (Engineer II / III ...)
    if LEVEL_RE.search(title):
        return False, "excluded: mid/senior level in title"

    # 3. Experience requirement in the description
    max_yrs = ec.get("max_years_experience", 2)
    for m in YEARS_RE.finditer(desc):
        if int(m.group(1)) > max_yrs:
            return False, f"excluded: requires {m.group(1)}+ years"

    # 4. Positive early-career signal?
    for s in ec.get("signals", []):
        if s.lower() in text:
            return True, f"early-career signal: '{s}'"

    # 5. No signal, no disqualifier = ambiguous level
    if ec.get("strict", False):
        return False, "excluded: no clear early-career signal (strict mode)"
    return True, "level unclear (kept — verify manually)"


def match(job, cfg):
    """Return (tier, groups, note) or (None, [], reason).

    tier: "strong" (role keyword in title) or "possible" (only in description).
    Job must ALSO pass the early-career filter to be kept.
    """
    title = _clean(job.get("title"))
    desc = _clean(job.get("description"))
    loc = (job.get("location") or "").lower()

    # generic title exclusions
    for bad in cfg.get("exclude_title", []):
        if bad.lower() in title:
            return None, [], f"excluded title '{bad}'"

    # location filter (skip if list empty; keep jobs with no location listed)
    locs = cfg.get("locations", [])
    if locs and loc and not any(l.lower() in loc for l in locs):
        return None, [], "location not in list"

    # role keyword matching
    hit_groups = []
    tier = None
    for group, keywords in cfg["roles"].items():
        for kw in keywords:
            k = kw.lower().strip()
            if k in title:
                hit_groups.append(group)
                tier = "strong"
                break
            elif k in desc:
                hit_groups.append(group)
                tier = tier or "possible"
                break
    if not hit_groups:
        return None, [], "no role keyword match"

    # early-career gate
    keep, note = is_early_career(job, cfg["early_career"])
    if not keep:
        return None, [], note

    return tier, sorted(set(hit_groups)), note
