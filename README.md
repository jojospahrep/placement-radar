# Placement Radar

Every open UK engineering internship and year-in-industry placement, pulled straight from employers' own
job boards, refreshed every 6 hours, with a weekly email digest.

Live site (once deployed): https://jojospahrep.github.io/placement-radar/

## How it works

```
 GitHub Actions cron (every 6h)                                       GitHub Pages
 ┌──────────────────────────────────────────────────────────────┐    ┌──────────────────┐
 │ radar/sources.py   Workday · Greenhouse · Ashby · Lever ·    │    │ site/index.html  │
 │                    SmartRecruiters public job-board APIs     │    │ site/app.js      │
 │        │  student-looking titles only                        │    │ search, filters, │
 │        ▼                                                     │    │ deadlines, signup│
 │ radar/classify.py  UK? role type? discipline? deadline?      │    └────────▲─────────┘
 │        ▼                                                     │             │
 │ radar/pipeline.py  merge into data/jobs.json, dedupe,        │  site/data/jobs.json
 │                    open/closed lifecycle, data/changes.jsonl ├──────────────┘
 │        ▼                                                     │  site/feed.xml (RSS)
 │ radar/export.py    public JSON + RSS                         │
 └──────────────────────────────────────────────────────────────┘
 GitHub Actions cron (Sun 18:00) → radar/digest.py → digests/DATE.md + Buttondown DRAFT → a human sends it
```

Design choices:

- **Employer APIs only, no aggregators.** Listings come from the public endpoints employers publish for their
  own careers pages. We don't scrape Gradcracker, Bright Network or LinkedIn.
- **No dependencies.** The pipeline is pure standard-library Python 3.10+, so the GitHub Action needs no install step.
- **Safe lifecycle.** A role closes only after 2 consecutive successful runs miss it, and never because its board
  errored. Non-UK postings are cached as rejects for 30 days, so repeat runs don't refetch their details.
- **Human in the loop for email.** The digest is created as a draft; nothing goes to subscribers unreviewed.

## Commands

```bash
python3 -m radar update                   # scrape everything, merge, rebuild site data
python3 -m radar update --only workday:dyson
python3 -m radar reclassify               # re-apply classify.py rules to stored jobs (offline)
python3 -m radar digest --no-draft        # write this week's digest locally
python3 -m radar health                   # list failing job boards
python3 -m unittest discover tests
python3 -m http.server 8765 -d site       # preview at http://localhost:8765
```

## Adding an employer

Open the employer's careers page and look at a job URL to see which system it runs on, then add a row to
`radar/companies.py` and run `python3 -m radar update --only <source>:<token>`:

| Job URL contains | List in companies.py | Token |
|---|---|---|
| `TENANT.wdN.myworkdayjobs.com/SITE` | `WORKDAY` | tenant, site, `wdN` |
| `boards.greenhouse.io/TOKEN` or `job-boards.greenhouse.io/TOKEN` | `GREENHOUSE` | token |
| `jobs.ashbyhq.com/NAME` | `ASHBY` | name |
| `jobs.lever.co/SLUG` | `LEVER` | slug |
| `jobs.smartrecruiters.com/COMPANY` | `SMARTRECRUITERS` | company |

## Configuration

| Where | What |
|---|---|
| `site/config.js` → `buttondownUser` | Buttondown username; turns on the signup form |
| Repo secret `BUTTONDOWN_API_KEY` | Lets the weekly job create the digest draft |
| `radar/export.py` → `SITE_URL` | Public URL used in the RSS feed and emails |
