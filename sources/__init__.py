"""ATS source fetchers. Each returns a list of normalized job dicts."""
from .greenhouse import fetch as fetch_greenhouse
from .ashby import fetch as fetch_ashby
from .workday import fetch as fetch_workday
from .lever import fetch as fetch_lever
from .smartrecruiters import fetch as fetch_smartrecruiters

FETCHERS = {
    "greenhouse": fetch_greenhouse,
    "ashby": fetch_ashby,
    "workday": fetch_workday,
    "lever": fetch_lever,
    "smartrecruiters": fetch_smartrecruiters,
}
