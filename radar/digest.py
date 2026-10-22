"""Weekly email digest: new roles since the last digest plus roles closing in the next 14 days.

Writes digests/YYYY-MM-DD.md. If BUTTONDOWN_API_KEY is set, it also creates a *draft* in Buttondown:
a person skims and sends it, so nothing goes to subscribers without review.
"""
import json
import os
import urllib.request
from datetime import date, timedelta

from .export import SITE_URL, board_jobs
from .http import USER_AGENT
from .pipeline import CHANGES, ROOT, load_store

DIGESTS = ROOT / "digests"
TYPE_LABEL = {"placement": "Year-in-industry placements", "internship": "Summer internships", "insight": "Insight & spring weeks"}


def last_digest_date() -> str:
    files = sorted(DIGESTS.glob("*.md"))
    return files[-1].stem if files else (date.today() - timedelta(days=7)).isoformat()


def _line(j: dict) -> str:
    dl = f" — **closes {date.fromisoformat(j['deadline']):%d %b}**" if j["deadline"] else ""
    return f"- [{j['company']}: {j['title']}]({j['url']}) · {j['location'].split(';')[0]}{dl}"


def build(today: date | None = None) -> tuple[str, str]:
    today = today or date.today()
    since = last_digest_date()
    jobs = {j["id"]: j for j in board_jobs(load_store(), today)}
    new_ids = set()
    if CHANGES.exists():
        for line in CHANGES.read_text().splitlines():
            c = json.loads(line)
            if c["event"] in ("new", "reopened") and c["at"][:10] >= since:
                new_ids.add(c["id"])
    new = [jobs[i] for i in new_ids if i in jobs]
    soon_cut = (today + timedelta(days=14)).isoformat()
    closing = sorted((j for j in jobs.values() if j["deadline"] and j["deadline"] <= soon_cut), key=lambda j: j["deadline"])

    subject = f"{len(new)} new UK engineering placements & internships" + (f", {len(closing)} closing soon" if closing else "")
    parts = [f"Hi! Here's what opened on [Placement Radar]({SITE_URL}) since {date.fromisoformat(since):%d %b}.\n"]
    if closing:
        parts.append("## ⏰ Closing in the next two weeks\n" + "\n".join(_line(j) for j in closing[:15]) + "\n")
    for t, label in TYPE_LABEL.items():
        group = sorted((j for j in new if j["type"] == t), key=lambda j: (j["company"], j["title"]))
        if group:
            parts.append(f"## {label} ({len(group)})\n" + "\n".join(_line(j) for j in group[:40]) + "\n")
    if not new:
        parts.append("No new roles this week. Deadlines above still apply.\n")
    parts.append(f"Browse and filter all {len(jobs)} open roles: {SITE_URL}\n\n"
                 "_Always check the employer's page for the exact deadline. Placement Radar is run by students and isn't affiliated with any employer._")
    return subject, "\n".join(parts)


def run(send_draft: bool = True) -> dict:
    subject, body = build()
    DIGESTS.mkdir(exist_ok=True)
    path = DIGESTS / f"{date.today().isoformat()}.md"
    path.write_text(f"# {subject}\n\n{body}")
    result = {"subject": subject, "file": str(path.relative_to(ROOT)), "draft": None}
    key = os.environ.get("BUTTONDOWN_API_KEY")
    if send_draft and key:
        req = urllib.request.Request(
            "https://api.buttondown.com/v1/emails",
            data=json.dumps({"subject": subject, "body": body, "status": "draft"}).encode(),
            headers={"Authorization": f"Token {key}", "Content-Type": "application/json", "User-Agent": USER_AGENT},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            result["draft"] = json.load(r).get("id")
    return result
