# API endpoints (draft for review)

All paths start with `/api`. JSON in, JSON out, ISO dates (`YYYY-MM-DD`). Every endpoint except `health`, `auth/register` and `auth/login` needs `Authorization: Bearer <token>` and returns **401** without it (NFR-5).

Errors always look like `{"error": {"code": "not_enough_data", "message": "Needs at least 2 check-ins"}}`.

**Status:** `GET /api/health`, `GET /api/users/{id}/metrics` and `GET /api/demo/metrics` exist (the last two have no login yet; they serve the simulated demo). Everything else is the plan, with the week it is built.

## Accounts

| Method and path | Purpose | Reqs | Week |
|---|---|---|---|
| GET `/health` | Server and database status | n/a | 1 (done) |
| POST `/auth/register` | Create account from email and password | FR-1 | 2 |
| POST `/auth/login` | Return a signed access token | FR-2 | 2 |
| POST `/auth/logout` | Client discards the token | FR-2 | 2 |
| GET `/me` | Current account | FR-2 | 2 |
| GET `/me/export` | Download all of the user's data as JSON | P-5 | 6 |
| DELETE `/me` | Delete the account and all its data | P-5 | 6 |

## Profile and snapshots

| Method and path | Purpose | Reqs | Week |
|---|---|---|---|
| POST `/onboarding` | Save the onboarding answers and create the baseline snapshot | FR-3, FR-4 | 2 |
| GET `/profile/current` | Latest snapshot | FR-4 | 2 |
| GET `/profile/snapshots?from=&to=` | List snapshots, newest first | FR-8 | 2 |
| GET `/profile/snapshots/{id}` | One snapshot | FR-8 | 2 |
| GET `/profile/at?date=` | Snapshot in effect on a date | FR-8 | 2 |

`POST /onboarding` accepts `weight`, `height`, `age`, `sex` (`male` or `female`), `activity_level` (`sedentary`, `light`, `moderate`, `very_active`, `extra_active`), `training_level` (`novice`, `intermediate`, `advanced`), `sleep_pattern`, `training_schedule` (`{"days": ["mon","wed","fri"]}`), `goal`, `diet_pattern`, and the optional `intake_kcal` or `deficit_level` (`small`, `moderate`, `large`). Age, sex, activity level and training level come from the changing requirements CR-1 to CR-5.

## Check-ins

| Method and path | Purpose | Reqs | Week |
|---|---|---|---|
| GET `/exercises?muscle_group=` | Exercise catalogue for the menus | FR-5 | 3 |
| GET `/plan/current` | Planned sessions this week, derived from the training schedule | FR-6 | 3 |
| POST `/checkins` | Save a weekly check-in (see below) | FR-5, FR-6, FR-7 | 3 |
| GET `/checkins?from=&to=` | List check-ins | FR-8 | 3 |
| GET `/checkins/{id}` | One check-in with its logs | FR-8 | 3 |

`POST /checkins` body:

```json
{
  "checkin_date": "2026-10-19",
  "weight": 72.4,
  "done_as_planned": ["mon", "wed"],
  "workouts": [{"exercise_id": 7, "sets": 3, "reps": 8, "weight_used": 60}],
  "sleep": {"bed_time": "23:00", "wake_time": "06:30"},
  "nutrition": {"protein_target_met": true, "notes": null}
}
```

Everything except `checkin_date` is optional. One request, one database transaction: it inserts a new profile snapshot (copy of the previous one with the new weight), then the check-in, then the logs. It returns `{"checkin_id": 12, "snapshot_id": 12}`. Fields for cardio and for `done_as_planned` depend on decisions D-1 and D-2.

## Metrics

| Method and path | Purpose | Reqs | Week |
|---|---|---|---|
| GET `/metrics/latest` | Latest value per metric, or `{"status": "not_enough_data"}` | FR-9, FR-12 | 3 |
| POST `/metrics/compute` | Recompute and store metrics (also runs after each check-in) | FR-9, NFR-4 | 3 |

## Recommendations

| Method and path | Purpose | Reqs | Week |
|---|---|---|---|
| POST `/recommendations` | Generate a suggestion. Body: `{"consent_llm": true}` | FR-13, NFR-1, NFR-6 | 4-5 |
| GET `/recommendations` | History of suggestions | FR-14 | 4 |
| GET `/recommendations/{id}` | One suggestion with its source metrics and rules | FR-14, NFR-7 | 4 |
| GET `/evidence-rules` | Read-only rule set with citations and version | NFR-7 | 4 |

If `consent_llm` is false or missing, the server uses the rule-based path and sends nothing to the external service (NFR-6). The same path runs when the service is down (P-4). The response includes `metrics[]`, `rules[]`, `estimate` (true for projections, shown as a range) and `generated_by` (`"rules"` or `"llm"`, which needs decision D-3).

## Simulation and evaluation

| Method and path | Purpose | Reqs | Week |
|---|---|---|---|
| POST and GET `/sim/personas` | Create and list personas | P-1 | 6 |
| POST `/sim/runs` | Run a persona through timepoints such as `["week_1", "week_6", "week_12"]` | P-1 | 6 |
| GET `/sim/compare?persona_id=&a=week_1&b=week_12` | Side-by-side profile and suggestions | P-1, FR-8 | 6 |

Evaluation is a command, not an endpoint: `python -m app.evaluation` (week 7) regenerates every number in the results chapter.

## Conventions to decide once

- **Passwords:** argon2 or bcrypt. **Tokens:** signed JWT with a short expiry.
- **Time zone:** store UTC, show local time on the client.
- **LLM calls:** only inside the server, never from the browser, and only with computed metrics, never email or user ID.


## Implemented now

`GET /api/users/{user_id}/metrics?as_of=YYYY-MM-DD` returns

```json
{"user_id": 1, "as_of": "2026-10-12",
 "metrics": [{"metric_type": "adherence_pct", "status": "ok", "value": 91.67, "unit": "%", "detail": {"weeks_used": 4}}]}
```

`as_of` defaults to the user's latest check-in date. A metric with too little data has `"status": "not_enough_data"` and `"value": null`. Unknown user: 404. Bad date: 422. `GET /api/demo/metrics` does the same for the simulated persona "Sam", creating it on first use.
