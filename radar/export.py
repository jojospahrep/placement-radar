"""Write the public files the static site reads: site/data/jobs.json, site/data/meta.json, site/feed.xml."""
import json
from datetime import date, datetime, timedelta, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

from .pipeline import ROOT, load_store

SITE = ROOT / "site"
SITE_URL = "https://jojospahrep.github.io/placement-radar/"


def board_jobs(store: dict, today: date | None = None) -> list[dict]:
    today_s = (today or date.today()).isoformat()
    out = []
    for j in store["jobs"].values():
        if j["status"] != "open" or j.get("duplicate_of") or (j.get("deadline") and j["deadline"] < today_s):
            continue
        out.append({
            "id": j["id"], "title": j["title"], "company": j["company"], "sector": j["sector"],
            "location": j["location"], "also_at": j.get("also_at", []), "type": j["type"],
            "disciplines": j["disciplines"], "deadline": j.get("deadline"), "cycle": j.get("cycle"),
            "url": j["url"], "first_seen": j["first_seen"][:10],
            "snippet": " ".join(j.get("description", "").split())[:220],
        })
    out.sort(key=lambda j: (j["deadline"] or "9999", j["company"], j["title"]))
    return out


def write_site(store: dict | None = None) -> dict:
    store = store or load_store()
    jobs = board_jobs(store)
    (SITE / "data").mkdir(parents=True, exist_ok=True)
    (SITE / "data" / "jobs.json").write_text(json.dumps(jobs, ensure_ascii=False, separators=(",", ":")))
    sources = store.get("sources", {})
    meta = {
        "updated_at": store.get("updated_at"),
        "open": len(jobs),
        "employers": len({j["company"] for j in jobs}),
        "employers_tracked": len(sources),
        "sources_ok": sum(s["ok"] for s in sources.values()),
        "by_type": {t: sum(j["type"] == t for j in jobs) for t in ("placement", "internship", "insight")},
    }
    (SITE / "data" / "meta.json").write_text(json.dumps(meta, indent=1))
    write_feed(jobs)
    return meta


def write_feed(jobs: list[dict]) -> None:
    cutoff = (date.today() - timedelta(days=14)).isoformat()
    recent = sorted((j for j in jobs if j["first_seen"] >= cutoff), key=lambda j: j["first_seen"], reverse=True)[:100]
    items = []
    for j in recent:
        pub = format_datetime(datetime.fromisoformat(j["first_seen"]).replace(tzinfo=timezone.utc))
        dl = f" · closes {j['deadline']}" if j["deadline"] else ""
        items.append(
            f"<item><title>{escape(j['company'])}: {escape(j['title'])}</title><link>{escape(j['url'])}</link>"
            f"<guid isPermaLink=\"false\">{j['id']}</guid><pubDate>{pub}</pubDate>"
            f"<description>{escape(j['type'].title() + ' · ' + j['location'] + dl)}</description></item>"
        )
    (SITE / "feed.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
        f"<title>Placement Radar: new UK engineering roles</title><link>{SITE_URL}</link>"
        "<description>New UK engineering internships and year-in-industry placements</description>"
        + "".join(items) + "</channel></rss>\n"
    )
