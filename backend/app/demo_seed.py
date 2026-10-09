"""Simulated persona for demos and tests (proposal P-1: the evaluation uses simulated users).

Run from backend/:  python -m app.demo_seed            (creates adaptfit.db if needed)
Safe to re-run: it does nothing if the demo user already exists.

Persona "Sam": 21-year-old novice, 175 cm, moderate activity, trains Mon/Wed/Fri, moderate deficit.
Six weekly check-ins from 2026-09-07 to 2026-10-12 with weight falling, mostly steady sleep and a squat that
progresses. Every number below is invented simulation data, not a real person's record.
"""
from __future__ import annotations

import json
import os
import sqlite3

from . import db

DEMO_EMAIL = "demo.sam@adaptfit.test"
PERSONA_NAME = "Sam (novice, moderate deficit)"

# (date, weight kg, sessions completed, bed, wake, squat (kg, reps) or None)
WEEKS = [
    ("2026-09-07", 74.4, ("mon", "wed", "fri"), "23:00", "06:30", (50, 8)),
    ("2026-09-14", 74.0, ("mon", "wed"),        "23:30", "06:30", (52.5, 8)),
    ("2026-09-21", 73.6, ("mon", "wed", "fri"), "23:15", "06:45", (55, 8)),
    ("2026-09-28", 73.1, ("mon", "fri"),        "00:00", "07:00", (57.5, 8)),
    ("2026-10-05", 72.7, ("mon", "wed", "fri"), "23:15", "06:30", (60, 8)),
    ("2026-10-12", 72.3, ("mon", "wed", "fri"), "23:00", "06:30", (62.5, 8)),
]
SCHEDULE = json.dumps({"days": ["mon", "wed", "fri"]})


def seed_demo(conn: sqlite3.Connection) -> int:
    """Create the demo persona and return its user_id."""
    row = conn.execute("SELECT user_id FROM users WHERE email = ?", (DEMO_EMAIL,)).fetchone()
    if row:
        return row["user_id"]
    uid = conn.execute("INSERT INTO users (email, password_hash) VALUES (?, 'not-a-real-hash')",
                       (DEMO_EMAIL,)).lastrowid
    squat = conn.execute("SELECT exercise_id FROM exercises WHERE name = 'Squat'").fetchone()[0]
    for day, weight, done, bed, wake, lift in WEEKS:
        sid = conn.execute(
            """INSERT INTO profile_snapshots (user_id, created_at, weight, height, sleep_pattern, training_schedule,
               goal, diet_pattern, age, sex, activity_level, training_level, deficit_level)
               VALUES (?, ?, ?, 175, '23:00-06:30', ?, 'lose_fat', 'balanced', 21, 'male', 'moderate', 'novice',
               'moderate')""", (uid, f"{day}T08:00:00.000Z", weight, SCHEDULE)).lastrowid
        cid = conn.execute("INSERT INTO checkins (user_id, snapshot_id, checkin_date) VALUES (?, ?, ?)",
                           (uid, sid, day)).lastrowid
        for session_day in done:
            conn.execute(
                "INSERT INTO workout_logs (checkin_id, exercise_id, session_day, sets, reps, weight_used) "
                "VALUES (?, ?, ?, 3, ?, ?)", (cid, squat, session_day, lift[1], lift[0]))
        conn.execute("INSERT INTO sleep_logs (checkin_id, bed_time, wake_time) VALUES (?, ?, ?)", (cid, bed, wake))
        conn.execute("INSERT INTO nutrition_logs (checkin_id, protein_target_met) VALUES (?, 1)", (cid,))
    conn.execute("INSERT OR IGNORE INTO personas (name, config_description) VALUES (?, ?)",
                 (PERSONA_NAME, "Novice, 21, 175 cm, trains Mon/Wed/Fri, moderate deficit, mostly steady sleep"))
    conn.commit()
    return uid


def find_demo_user(conn: sqlite3.Connection):
    row = conn.execute("SELECT user_id FROM users WHERE email = ?", (DEMO_EMAIL,)).fetchone()
    return row["user_id"] if row else None


if __name__ == "__main__":
    path = os.getenv("ADAPTFIT_DB", "adaptfit.db")
    connection = db.connect(path)
    db.init_db(connection)
    print(f"Demo persona ready in {path}: user_id={seed_demo(connection)}")
    connection.close()
