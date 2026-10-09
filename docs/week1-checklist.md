# Status checklist (updated 9 Oct 2026)

| # | Task | Status | What is left for you |
|---|---|---|---|
| 1 | Repo, structure, CI | Ready | Push to GitHub (README), check CI is green |
| 2 | Requirements as tickets and board | 42 tickets written | Run `scripts/create_issues.py --run` after `gh auth login` |
| 3 | Figma wireframes | Complete, prototype links listed in `docs/prototype-flows.md` | Export the PDF into `docs/design/`, upload the design, paste the Figma link |
| 4 | Database schema | Done, schema version 2 | Settle D-1, D-3, D-5, D-8 |
| 5 | API endpoint list | Written; metrics endpoints built | Review |
| 6 | Metric formulas | **Done** (`docs/metrics.md`) | Source the strength benchmark from Ralston et al. |
| 7 | Ethics and checkpoint | Message drafted | Send it |
| 8 | Questionnaire | Draft written | Pilot with two people |
| 9 | Hello world end to end | Frontend skeleton for all frames | Run the README steps on your machine |

## What was verified and what was not
Verified here: the database schema and all metric code (53 unit tests, 2 skipped without FastAPI); the front end bundles and every frame renders on the server; the Figma tap map matches `flows.js` (`npm run check:flows`). **Not verified**: the FastAPI server and the live React page in a browser, because this build environment blocks package installs. Your first run is the real check. Written for Python 3.14 and Node 24.
