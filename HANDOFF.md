# Handoff: Placement Radar

Status as of 2026-10-22 (end of first build session). Read this first if you are picking the work up.

## Done and verified locally
- Pipeline (`radar/`): 82 employer job boards (48 Workday, 23 Greenhouse, 6 Ashby, 1 Lever, 4 SmartRecruiters).
  First run returned 73 UK engineering roles (43 year placements, 30 internships) from 18 employers, with 0 failing boards.
- Classification: UK filter, placement/internship/insight, 11 discipline tags, non-engineering roles dropped,
  deadline and cycle extraction. 15 unit tests pass (`python3 -m unittest discover tests`).
- Lifecycle: new/closed/reopened events in `data/changes.jsonl`, dedupe across cities, reject cache for non-UK roles.
- Site (`site/`): search, type chips, discipline/sector/region filters, sort, "new" and "closing soon" badges,
  RSS, signup form. Checked in a browser at desktop and phone width, with no console errors.
- Digest (`radar/digest.py`): markdown digest plus optional Buttondown draft.
- GitHub Actions: `update.yml` (every 6h: test, scrape, commit data, deploy Pages) and `digest.yml` (Sun 18:00).

## Waiting on Joseph (needs his accounts)
1. Live as a quiet BETA since 2026-10-23: public repo, Pages deployed by Actions (repo variable DEPLOY_PAGES=true).
   The page has `noindex` and a Beta label; Joseph is not publicising it yet. Remove the noindex line in
   site/index.html when he decides to launch properly.
2. Create a free Buttondown account. Put the username in `site/config.js` and add the API key as the repo secret
   `BUTTONDOWN_API_KEY`.
3. Pick a contact email or domain. For now the footer links to GitHub issues for problems and removal requests.

## Next build steps (no input needed)
- More employers on other systems: BAE Systems, Airbus, Arup, JLR, Atkins, Mott MacDonald, AECOM, National Grid,
  Jacobs and McLaren use SuccessFactors, Oracle, Eightfold or Avature. Each needs a small adapter in `radar/sources.py`.
- Rolls-Royce returns only 1 role: its early-careers roles are probably on a separate Workday site. Find it.
- Privacy-friendly analytics (e.g. GoatCounter) to measure the validation targets (200 signups, 10 payers).
- Per-discipline landing pages (`/mechanical/`, `/aerospace/`…) for search traffic.
- Later: a paid instant-alert tier via a Stripe Payment Link.
