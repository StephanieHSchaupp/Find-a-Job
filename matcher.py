"""Decide whether a job matches your target roles, is the right discipline (EE),
and is early-career.

WHAT CHANGED (and why it matters):

1. Matching is now WHOLE-WORD, not substring. The old code used `kw in text`,
   which silently produced garbage:
       "gan"  matched "orGANization"      -> nearly every job was a "power" match
       "sic"  matched "phySICs", "baSIC"
       "ate " matched "graduATE ", "associATE "
       "iv"   matched "drIVe"             -> "Motor Drive Engineer" was REJECTED
       "ca"   matched "chiCAgo", "CAnada" -> the location filter did nothing
   Every list in config.yaml is now matched on word boundaries.

2. New `discipline:` block — a block-list plus an EE gate. This is what keeps
   mechanical / thermal / structural / finance / ops roles out.

3. Roman-numeral level detection only fires on a trailing level token, so
   "V&V Engineer" is no longer read as "Engineer V".

4. Years-of-experience rejection now requires experience-ish words nearby, so
   "founded 10 years ago" doesn't kill a posting.
"""
import re
from functools import lru_cache

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")

# Trailing level token: "Engineer II", "Engineer III, Power", "Systems Eng IV -"
# The (?![\w&]) guard keeps "V&V Engineer" from being read as level V.
LEVEL_RE = re.compile(
    r"(?<![&\w])(?:ii|iii|iv|v)(?![\w&])(?=\s*(?:$|[,\-–(/]))", re.I
)
# "Engineer 2", "Level 3", "Grade 4"
LEVEL_NUM_RE = re.compile(r"\b(?:engineer|eng|level|lvl|grade)\s*[-–]?\s*[2-9]\b", re.I)

# "5+ years", "3-5 years", "minimum of 4 years"
YEARS_RE = re.compile(r"(\d{1,2})\s*(?:\+|-|–|—|to|or)?\s*(?:\d{1,2})?\s*\+?\s*years?\b", re.I)
# ...but only counts if it's talking about *experience*, not company age.
EXP_CTX_RE = re.compile(
    r"experien|industry|professional|relevant|hands[\s-]?on|background|working", re.I
)

# Separators allowed *inside* a keyword: "dc-dc" also matches "dc dc" / "dcdc".
_SEP = r"[\s\-_/.]*"


def _clean(text):
    return WS_RE.sub(" ", TAG_RE.sub(" ", text or "")).lower()


@lru_cache(maxsize=8192)
def _kw_re(kw):
    """Compile a config keyword into a whole-word regex.

    Word boundaries are only applied where the keyword's edge is alphanumeric,
    so keywords like "v&v" and "sr." still work.
    """
    kw = (kw or "").strip().lower()
    if not kw:
        return None
    parts = [p for p in re.split(r"[\s\-_/]+", kw) if p]
    if not parts:
        return None
    body = _SEP.join(re.escape(p) for p in parts)
    left = r"(?<![a-z0-9])" if kw[0].isalnum() else ""
    right = r"(?![a-z0-9])" if kw[-1].isalnum() else ""
    return re.compile(left + body + right, re.I)


def _first(keywords, text):
    """Return the first keyword that occurs as a whole word in `text`, else None."""
    if not text:
        return None
    for kw in keywords or []:
        rx = _kw_re(kw)
        if rx and rx.search(text):
            return kw
    return None


# --------------------------------------------------------------------------
# Discipline gate — this is the mechanical / finance / non-EE filter
# --------------------------------------------------------------------------
def discipline_ok(job, cfg):
    """Return (keep: bool, note: str)."""
    d = cfg.get("discipline") or {}
    if not d.get("enabled", True):
        return True, ""

    title = _clean(job.get("title"))
    desc = _clean(job.get("description"))
    text = f"{title} {desc}"

    bad = _first(d.get("exclude_title"), title)
    if bad:
        return False, f"wrong discipline: title has '{bad}'"

    bad = _first(d.get("exclude_text"), text)
    if bad:
        return False, f"wrong discipline: '{bad}'"

    signals = d.get("ee_signals") or []
    if not signals:
        return True, ""

    hit = _first(signals, title)
    if hit:
        return True, f"EE (title: '{hit}')"

    if (d.get("ee_gate") or "title_or_description").lower() == "title":
        return False, "no EE signal in title"

    if desc.strip():
        hit = _first(signals, desc)
        if hit:
            return True, f"EE (description: '{hit}')"
        return False, "no EE signal in title or description"

    # Workday / SmartRecruiters feeds return no description at all.
    # A discipline-neutral title ("Systems Engineer") can't be verified -> drop it.
    amb = _first(d.get("ambiguous_titles"), title)
    if amb:
        return False, f"ambiguous title '{amb}' and no description to verify EE"
    if d.get("allow_when_no_description", True):
        return True, "EE unverified (feed has no description)"
    return False, "no description to verify EE"


def location_ok(job, cfg):
    loc = _clean(job.get("location"))
    if not loc:
        return True, ""  # keep jobs with no location listed
    bad = _first(cfg.get("exclude_locations"), loc)
    if bad:
        return False, f"location excluded ('{bad}')"
    locs = cfg.get("locations") or []
    if locs and not _first(locs, loc):
        return False, "location not in list"
    return True, ""


# --------------------------------------------------------------------------
# Early-career gate
# --------------------------------------------------------------------------
def is_early_career(job, ec):
    """Return (keep: bool, note: str). `ec` is the early_career config block."""
    title = _clean(job.get("title"))
    desc = _clean(job.get("description"))
    text = f"{title} {desc}"

    bad = _first(ec.get("seniority_exclusions"), title)
    if bad:
        return False, f"excluded: title contains '{bad}'"

    if LEVEL_RE.search(title) or LEVEL_NUM_RE.search(title):
        return False, "excluded: mid/senior level in title"

    max_yrs = ec.get("max_years_experience", 2)
    for m in YEARS_RE.finditer(desc):
        yrs = int(m.group(1))
        if yrs <= max_yrs:
            continue
        window = desc[max(0, m.start() - 60): m.end() + 80]
        if EXP_CTX_RE.search(window):
            return False, f"excluded: requires {yrs}+ years"

    hit = _first(ec.get("signals"), text)
    if hit:
        return True, f"early-career signal: '{hit}'"

    if ec.get("strict", False):
        return False, "excluded: no clear early-career signal (strict mode)"
    return True, "level unclear (kept — verify manually)"


# --------------------------------------------------------------------------
def match(job, cfg):
    """Return (tier, groups, note) or (None, [], reason).

    tier: "strong" (role keyword in title) or "possible" (only in description).
    A job must pass: exclude_title -> location -> discipline -> role -> early-career.
    """
    title = _clean(job.get("title"))
    desc = _clean(job.get("description"))

    bad = _first(cfg.get("exclude_title"), title)
    if bad:
        return None, [], f"excluded title '{bad}'"

    ok, why = location_ok(job, cfg)
    if not ok:
        return None, [], why

    ok, disc_note = discipline_ok(job, cfg)
    if not ok:
        return None, [], disc_note

    hit_groups = []
    tier = None
    for group, keywords in (cfg.get("roles") or {}).items():
        if _first(keywords, title):
            hit_groups.append(group)
            tier = "strong"
        elif _first(keywords, desc):
            hit_groups.append(group)
            tier = tier or "possible"
    if not hit_groups:
        return None, [], "no role keyword match"

    keep, note = is_early_career(job, cfg.get("early_career") or {})
    if not keep:
        return None, [], note

    if disc_note:
        note = f"{note} | {disc_note}"
    return tier, sorted(set(hit_groups)), note
