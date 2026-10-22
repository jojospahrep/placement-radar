"""Fetch every source, classify, deduplicate, and merge into the job store.

Store: data/jobs.json  {"jobs": {id: job}, "sources": {source_id: {...health...}}}
Every new or closed role is appended to data/changes.jsonl, which the digest reads.
A role is closed only after MISSES_BEFORE_CLOSE consecutive successful runs that did not return it,
and never because its source failed, so one flaky request cannot wipe the board.
"""
import concurrent.futures as cf
import hashlib
import json
import re
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import classify
from .sources import all_sources

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "data" / "jobs.json"
CHANGES = ROOT / "data" / "changes.jsonl"
MISSES_BEFORE_CLOSE = 2
REJECT_TTL_DAYS = 30
DETAIL_SOURCES = {"workday", "smartrecruiters"}  # adapters that pay a request per posting


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_store() -> dict:
    if STORE.exists():
        return json.loads(STORE.read_text())
    return {"jobs": {}, "sources": {}}


def save_store(store: dict) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(store, indent=1, sort_keys=True, ensure_ascii=False) + "\n")


def job_id(raw: dict) -> str:
    return hashlib.sha1(raw["url"].split("?")[0].encode()).hexdigest()[:12]


def dedupe_key(job: dict) -> str:
    """Same employer + same normalised title = one card, even if posted to several cities or boards."""
    t = re.sub(r"\b(20\d\d(/\d\d)?|uk|united kingdom|london|bristol|cambridge|[-–(),/|])\b", " ", job["title"].lower())
    return f"{job['company'].lower()}|{' '.join(re.sub(r'[^a-z0-9 ]', ' ', t).split())}"


def enrich(raw: dict, today: date) -> dict | None:
    """Turn a raw posting into a board job, or None if it doesn't belong on a UK engineering board."""
    if not classify.is_uk(raw["location"], raw.get("country", "")) and not (
        raw.get("country") == "" and classify.is_uk(raw["description"][:400])
    ):
        return None
    kind = classify.role_type(raw["title"], raw["description"])
    if not kind:
        return None
    tags = classify.disciplines(raw["title"], raw["description"])
    if not classify.is_engineering(raw["title"], tags):
        return None
    text = f"{raw['title']}\n{raw['description']}"
    return {
        **{k: raw[k] for k in ("company", "sector", "source", "title", "location", "url", "description", "posted")},
        "country": raw.get("country", ""),
        "type": kind,
        "disciplines": tags or ["General Engineering"],
        "deadline": raw.get("deadline") or classify.find_deadline(text, today),
        "cycle": classify.find_cycle(text),
    }


def fetch_all(store: dict, workers: int = 16, only: str | None = None):
    known = {u: {"reject": True} for u in store.get("rejects", {})}
    known.update({j["url"]: j for j in store["jobs"].values()})
    results, health = {}, {}
    srcs = [s for s in all_sources() if not only or only in s[0]]

    def run(src):
        sid, name, fn = src
        try:
            return sid, name, fn(known), None
        except Exception as e:  # one broken board must not stop the rest
            return sid, name, [], f"{type(e).__name__}: {e}"

    with cf.ThreadPoolExecutor(workers) as ex:
        for sid, name, raws, err in ex.map(run, srcs):
            results[sid] = raws
            health[sid] = {"company": name, "ok": err is None, "error": err, "raw": len(raws), "checked": now_iso()}
            print(f"{'ok ' if not err else 'ERR'} {sid:42} {len(raws):4} student-type{'  ' + err if err else ''}", flush=True)
    return results, health


def merge(store: dict, results: dict, health: dict, today: date | None = None) -> dict:
    today = today or date.today()
    ts = now_iso()
    jobs = store["jobs"]
    changes = []
    seen_ids = set()
    rejects = store.setdefault("rejects", {})
    for sid, raws in results.items():
        for raw in raws:
            job = enrich(raw, today)
            if not job:
                if raw["source"] in DETAIL_SOURCES:
                    rejects[raw["url"]] = ts
                continue
            jid = job_id(raw)
            seen_ids.add(jid)
            old = jobs.get(jid)
            if old is None:
                job.update(id=jid, source_id=sid, first_seen=ts, last_seen=ts, status="open", misses=0)
                jobs[jid] = job
                changes.append({"event": "new", "id": jid, "at": ts})
            else:
                reopened = old["status"] == "closed"
                old.update(job, last_seen=ts, status="open", misses=0, source_id=sid)
                if reopened:
                    changes.append({"event": "reopened", "id": jid, "at": ts})

    ok_sources = {sid for sid, h in health.items() if h["ok"]}
    for jid, job in jobs.items():
        if jid in seen_ids or job["status"] != "open" or job.get("source_id") not in ok_sources:
            continue
        job["misses"] = job.get("misses", 0) + 1
        if job["misses"] >= MISSES_BEFORE_CLOSE:
            job.update(status="closed", closed_at=ts)
            changes.append({"event": "closed", "id": jid, "at": ts})
        elif job.get("deadline") and job["deadline"] < today.isoformat():
            job.update(status="closed", closed_at=ts)
            changes.append({"event": "closed", "id": jid, "at": ts})

    # Mark duplicates: keep the earliest-seen card per dedupe key, hide the rest from the board.
    groups = {}
    for job in sorted(jobs.values(), key=lambda j: j["first_seen"]):
        if job["status"] == "open":
            groups.setdefault(dedupe_key(job), []).append(job)
    for group in groups.values():
        primary = group[0]
        primary.pop("duplicate_of", None)
        primary["also_at"] = sorted({loc for j in group[1:] for loc in [j["location"]] if loc and loc != primary["location"]})
        for j in group[1:]:
            j["duplicate_of"] = primary["id"]

    # Forget rejects not seen for a month so the cache stays small and rule changes eventually re-check them.
    cutoff = (datetime.now(timezone.utc) - timedelta(days=REJECT_TTL_DAYS)).isoformat()
    for u in [u for u, t in rejects.items() if t < cutoff]:
        del rejects[u]

    store["sources"].update(health)
    store["updated_at"] = ts
    if changes:
        CHANGES.parent.mkdir(parents=True, exist_ok=True)
        with CHANGES.open("a") as f:
            for c in changes:
                f.write(json.dumps(c) + "\n")
    return {"new": sum(c["event"] == "new" for c in changes), "closed": sum(c["event"] == "closed" for c in changes),
            "open": sum(j["status"] == "open" and not j.get("duplicate_of") for j in jobs.values()),
            "sources_ok": len(ok_sources), "sources_failed": len(health) - len(ok_sources)}


def update(only: str | None = None) -> dict:
    store = load_store()
    results, health = fetch_all(store, only=only)
    summary = merge(store, results, health)
    save_store(store)
    return summary


def reclassify() -> dict:
    """Re-run classification over stored jobs after changing rules in classify.py (no network)."""
    store = load_store()
    today = date.today()
    dropped = 0
    for jid, job in list(store["jobs"].items()):
        new = enrich({**job, "deadline": job.get("deadline") if job["source"] == "greenhouse" else None}, today)
        if new is None:
            del store["jobs"][jid]
            store.setdefault("rejects", {})[job["url"]] = now_iso()
            dropped += 1
        else:
            job.update(new)
    save_store(store)
    return {"dropped": dropped, "kept": len(store["jobs"])}


if __name__ == "__main__":
    try:
        print(update())
    except Exception:
        traceback.print_exc()
        raise
