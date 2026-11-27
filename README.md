# AdaptFit

A continuously adaptive, wearable-free AI fitness profiling and coaching prototype (SWE3090 final class project, USIU).

- **Backend:** Python 3.14, FastAPI, SQLite
- **Frontend:** React 18 with Vite (Node 24)
- **Trend engine:** `backend/app/metrics.py`, pure functions; the LLM explains the numbers, it never computes them
- **Docs:** `docs/` (metrics, changing requirements, prototype flows, schema, API plan, tickets)

## First-time setup

### 1. Git and GitHub
```bash
git init
git add .
git commit -m "Initial commit: AdaptFit project"
git branch -M main
git remote add origin <your empty GitHub repo URL>
git push -u origin main
```
Create the repo on GitHub first (no README, no .gitignore). Push at the end of every working day: backups are required.

### 2. Backend (terminal 1)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m unittest discover -s tests -v     # 53 tests; 2 are skipped only if FastAPI is missing
python -m app.demo_seed                     # optional: creates the simulated persona "Sam"
uvicorn app.main:app --reload --port 8000
```
Open http://localhost:8000/api/health. Expected: `{"status":"ok","database":"ok","tables":14,"schema_version":2}`.
Open http://localhost:8000/api/demo/metrics to see every metric computed for the demo persona.
Interactive API docs: http://localhost:8000/docs.

### 3. Frontend (terminal 2)
```bash
cd frontend
npm install
npm run check:flows                # checks the app matches the Figma tap map
npm run dev                        # http://localhost:5173
```
- http://localhost:5173/#/status is the connection check (Client, Server, Database all "Working").
- http://localhost:5173/#/index lists every wireframe frame; `#/03a` is the Home screen with live metrics.
- The app opens on frame 01a; tapping through follows `docs/prototype-flows.md`.



## Folder map

| Path | What it is |
|---|---|
| `backend/db/schema.sql`, `seed.sql` | Database schema (version 2) and exercise catalogue |
| `backend/app/metrics.py` | The metric formulas (pure functions) |
| `backend/app/metrics_service.py` | Reads logs from the database, runs the formulas, builds the API report |
| `backend/app/demo_seed.py` | Simulated persona for demos and tests |
| `backend/app/main.py` | FastAPI app |
| `backend/tests/` | Unit tests (schema, metrics, demo) |
| `frontend/src/flows.js` | Frame map that mirrors the Figma prototype |
| `frontend/src/screens/` | Home (live metrics) and Status screens |
| `docs/metrics.md` | Every formula, minimum data and worked example |
| `docs/changing-requirements.md` | CR-1 to CR-9 |
| `docs/prototype-flows.md` | Figma tap connections |
| `docs/design/` | Where the exported wireframes and Figma link go |
| `docs/schema-notes.md`, `api.md` | Decisions and endpoint plan |
| `docs/week1-checklist.md` | Current status: done, left, verified |
| `.vscode/` | Tasks, debug config, recommended extensions |

Never commit `.env` or a real API key. Copy `.env.example` to `.env` when the LLM layer starts.

Rule
R1	Neither adherence nor weight trend has enough data	Log one more check-in; numbers appear after two weeks	Brand new user, 1 check-in
R2	Losing weight faster than planned on two check-ins in a row (ratio above 1.25x)	A smaller deficit keeps muscle and is easier to sustain	Ratio 1.6x now and last time
R3	Adherence below 60%	Try a smaller plan for two weeks, never fewer than 2 sessions a week	50% of 12 sessions: suggests 2 a week
R4	Bed and wake times vary by more than 45 minutes	Keep both within 30 minutes of the same time	70 minute spread
R5	Losing more slowly than planned (ratio below 0.75x)	Common early on; check intake; wait two more weeks	Ratio 0.4x
R6	Adherence at least 80% and strength going up	Add one rep to each set, or the smallest weight increase	92% and bench +2.5% a week
R7	Nothing above applied	Nothing needs changing, keep the plan	70% adherence, normal trend
