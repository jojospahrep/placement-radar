"""Adapters for each public job-board API. Every adapter returns a list of raw postings:

    {company, sector, source, title, location, country, url, description, posted, deadline}

Only postings whose title looks like a student role are kept, so detail requests stay few.
`known` maps url -> previously stored job; adapters reuse its description instead of refetching.
"""
import urllib.parse

from . import companies
from .classify import html_to_text, role_type
from .http import get_json, post_json

WORKDAY_QUERIES = ["intern", "internship", "placement", "industrial placement", "year in industry", "summer", "student"]


def _raw(company, sector, source, title, location, url, description="", country="", posted="", deadline=None):
    return dict(company=company, sector=sector, source=source, title=title.strip(), location=location or "",
                country=country or "", url=url, description=description, posted=posted or "", deadline=deadline)


def workday(name, sector, tenant, site, host, known):
    base = f"https://{tenant}.{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}"
    seen = {}
    for q in WORKDAY_QUERIES:
        offset = 0
        while offset < 400:
            d = post_json(base + "/jobs", {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": q})
            posts = d.get("jobPostings") or []
            for p in posts:
                if p.get("title") and role_type(p["title"]) and p.get("externalPath"):
                    seen.setdefault(p["externalPath"], p)
            offset += 20
            if not posts or offset >= (d.get("total") or 0):
                break
    out = []
    for path, p in seen.items():
        url = f"https://{tenant}.{host}.myworkdayjobs.com/en-US/{site}{path}"
        k = known.get(url)
        if k and k.get("reject"):
            continue
        if k and k.get("description"):
            out.append(_raw(name, sector, "workday", p["title"], k["location"], url, k["description"], k.get("country", ""),
                            k.get("posted", "")))
            continue
        try:
            info = get_json(base + path)["jobPostingInfo"]
        except Exception:
            continue
        country = ((info.get("jobRequisitionLocation") or {}).get("country") or {}).get("alpha2Code", "")
        loc = info.get("location") or p.get("locationsText", "")
        extra = ", ".join(info.get("additionalLocations") or [])
        out.append(_raw(name, sector, "workday", info.get("title", p["title"]), f"{loc}{'; ' + extra if extra else ''}", url,
                        html_to_text(info.get("jobDescription", "")), country, info.get("startDate", "")))
    return out


def greenhouse(name, sector, token, known):
    d = get_json(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true")
    out = []
    for j in d.get("jobs", []):
        if not role_type(j["title"]):
            continue
        locs = [j.get("location", {}).get("name", "")] + [o.get("location") or "" for o in j.get("offices", [])]
        out.append(_raw(name, sector, "greenhouse", j["title"], "; ".join(dict.fromkeys(l for l in locs if l)),
                        j["absolute_url"], html_to_text(j.get("content", "")), posted=(j.get("first_published") or "")[:10],
                        deadline=(j.get("application_deadline") or None) and j["application_deadline"][:10]))
    return out


def ashby(name, sector, board, known):
    d = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{board}")
    out = []
    for j in d.get("jobs", []):
        if not role_type(j["title"]) or not j.get("isListed", True):
            continue
        locs = [j.get("location", "")] + [s.get("location", "") for s in j.get("secondaryLocations", [])]
        out.append(_raw(name, sector, "ashby", j["title"], "; ".join(l for l in locs if l), j["jobUrl"],
                        j.get("descriptionPlain", ""), posted=(j.get("publishedAt") or "")[:10]))
    return out


def lever(name, sector, slug, known):
    d = get_json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    out = []
    for j in d:
        if not role_type(j["text"]):
            continue
        cats = j.get("categories", {})
        locs = cats.get("allLocations") or [cats.get("location", "")]
        out.append(_raw(name, sector, "lever", j["text"], "; ".join(locs), j["hostedUrl"], j.get("descriptionPlain", ""),
                        j.get("country", "")))
    return out


def smartrecruiters(name, sector, company, known):
    seen = {}
    for q in ["intern", "placement", "student", "summer", "industrial"]:
        d = get_json(f"https://api.smartrecruiters.com/v1/companies/{company}/postings?"
                     + urllib.parse.urlencode({"q": q, "country": "gb", "limit": 100}))
        for j in d.get("content", []):
            if role_type(j["name"]):
                seen[j["id"]] = j
    out = []
    for jid, j in seen.items():
        url = f"https://jobs.smartrecruiters.com/{company}/{jid}"
        k = known.get(url) or {}
        if k.get("reject"):
            continue
        desc = k.get("description", "")
        if not desc:
            try:
                sec = get_json(j["ref"]).get("jobAd", {}).get("sections", {})
                desc = html_to_text(" ".join((sec.get(s) or {}).get("text", "") for s in ("jobDescription", "qualifications", "additionalInformation")))
            except Exception:
                pass
        loc = j.get("location", {})
        out.append(_raw(name, sector, "smartrecruiters", j["name"], loc.get("fullLocation") or loc.get("city", ""), url, desc,
                        loc.get("country", ""), (j.get("releasedDate") or "")[:10]))
    return out


def all_sources():
    """(source id, callable(known) -> list) for every configured employer."""
    for n, s, t, site, h in companies.WORKDAY:
        yield f"workday:{t}", n, lambda known, a=(n, s, t, site, h): workday(*a, known)
    for n, s, t in companies.GREENHOUSE:
        yield f"greenhouse:{t}", n, lambda known, a=(n, s, t): greenhouse(*a, known)
    for n, s, t in companies.ASHBY:
        yield f"ashby:{t}", n, lambda known, a=(n, s, t): ashby(*a, known)
    for n, s, t in companies.LEVER:
        yield f"lever:{t}", n, lambda known, a=(n, s, t): lever(*a, known)
    for n, s, t in companies.SMARTRECRUITERS:
        yield f"smartrecruiters:{t}", n, lambda known, a=(n, s, t): smartrecruiters(*a, known)
