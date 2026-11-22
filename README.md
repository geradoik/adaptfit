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

### 4. Optional: load the tickets
```bash
gh auth login
python scripts/create_issues.py          # dry run
python scripts/create_issues.py --run    # creates 42 issues and 8 milestones (run once)
```

### In VS Code
Accept the recommended extensions. **Terminal > Run Task** has: Backend: run tests, Backend: run API, Frontend: run dev server, and **Run everything (demo)**, which starts both servers. F5 debugs the API.

## If something fails
- **`pip install` fails building pydantic-core on Python 3.14:** upgrade pip (`python -m pip install -U pip`) and retry. If it still fails, use Python 3.13 for the venv; nothing in the code needs 3.14.
- **PowerShell will not activate the venv:** run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
- **Old `adaptfit.db` and errors about missing columns:** delete `backend/adaptfit.db` and restart; the schema is now version 2.
- **Front end shows "Could not reach the server":** the backend is not running on port 8000.

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

## Validation helpers

Added a new folder, `adaptfit_helpers/`, with:

- `validation.py`: two input checks, `validate_number_in_range` and `validate_choice`
- `test_validation.py`: 8 unit tests for them

Run the tests from the top folder with `python -m pytest adaptfit_helpers`.