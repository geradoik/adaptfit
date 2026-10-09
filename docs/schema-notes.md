# Schema notes

`backend/db/schema.sql` implements the ER diagram (Figure 4.3) table for table: 14 tables, same names, keys and relationships. Beyond the diagram it adds only constraints that enforce rules already in your requirements:

- Snapshots cannot be updated, only inserted (FR-7). A trigger blocks `UPDATE`.
- A check-in must use a snapshot that belongs to the same user (composite foreign key).
- One check-in per snapshot, one nutrition log and one sleep log per check-in (the `1` and `0..1` labels in the diagram).
- Deleting a user deletes everything about them but keeps the shared exercise catalogue (supports the privacy requirements).

`backend/tests/test_schema.py` checks every one of these (15 tests).

## Decisions to settle this week

Writing the schema, API and wireframes exposed gaps between the ER diagram and the requirements. None of them need a new table. Each is an extra column or a convention. Settle them now, because the scope locks after the presentation and several block week 2-3 tickets. Whatever you accept, update Figure 4.3 and `schema.sql` together (there is no real data yet, so edit the file and delete `adaptfit.db`).

| ID | Gap | Recommendation | Blocks |
|---|---|---|---|
| D-1 | Cardio is logged by intensity and duration band in the check-in design, but `workout_logs` only has sets, reps and weight. | Add nullable `duration_min` and `intensity` to `workout_logs`, and add cardio rows (walking, running, cycling) to `exercises` with muscle group `cardio`. | T-14 (week 3) |
| D-2 | Adherence is completed sessions divided by scheduled sessions, but nothing records which planned session a log belongs to. A session with four exercises would count four times. | Add nullable `session_day` (the planned day) to `workout_logs`. Completed sessions are then the distinct `(checkin_id, session_day)` pairs. | T-06, T-16 |
| D-3 | The app needs to label a suggestion as rules-only or AI-written, and the evaluation compares the two. The `recommendations` table cannot say which. | Add `source` (`'rules'` or `'llm'`) to `recommendations`. | T-23, T-36 |
| D-4 | Simulated personas need user accounts. | No schema change: persona accounts use the email pattern `persona-N@sim.local`, and reports filter on that suffix. | T-29 |
| D-5 | `sleep_logs` holds one bed and wake time per check-in, but sleep consistency is variability across nights. | Decide in the metric formulas: either measure variability across weekly check-ins, or drop `UNIQUE` on `sleep_logs.checkin_id` and allow several nights per check-in. | T-06, T-19 |
| D-6 | Schema allows only one check-in per user per date. | Keep it (clean weekly cadence). Simulated personas must use distinct dates. | none |
| D-7 | FR-3 asks for the user's diet pattern at onboarding, but `profile_snapshots` has no diet column. | Add `diet_pattern TEXT` to `profile_snapshots`. | T-11 (week 2) |

Items D-1, D-2, D-3 and D-7 are additive columns, so the existing tests keep passing.

## Moving to PostgreSQL later

SQLite is fine for development and for the demo. If you switch:

- `INTEGER PRIMARY KEY AUTOINCREMENT` becomes `GENERATED ALWAYS AS IDENTITY`.
- Text timestamps become `TIMESTAMPTZ DEFAULT now()` (replace the `strftime` defaults).
- Drop the two `PRAGMA` lines.
- `INSERT OR IGNORE` becomes `INSERT ... ON CONFLICT DO NOTHING`.
- The immutability trigger needs a small PL/pgSQL function that raises an exception.
- Constraints, foreign keys and indexes carry over unchanged.


## Applied 9 Oct 2026
- **D-2 applied**: `workout_logs.session_day` (mon..sun, nullable).
- **D-7 applied**: `profile_snapshots.diet_pattern`.
- `training_schedule` format is now `{"days": ["mon","wed","fri"]}`.
- Still open: D-1, D-3, D-5.

- **Changing requirements CR-1 to CR-5 applied**: `profile_snapshots` gained nullable `age`, `sex`, `activity_level`, `training_level`, `deficit_level`, `intake_kcal`. Schema version is now 2. A database file created earlier does not gain the columns (the schema only creates missing tables), so delete `backend/adaptfit.db` once and restart. Update the ER diagram.
- **D-8 (new)**: onboarding must ask for age and sex, otherwise BMR returns `not_enough_data`.
