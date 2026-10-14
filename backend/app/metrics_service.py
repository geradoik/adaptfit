"""Reads logs from the database, calls the pure functions in metrics.py, stores results (FR-9).

Only results with status "ok" are written to the metrics table. not_enough_data is returned
to the caller but never stored, so an empty history cannot look like a measured zero.
"""
from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import date, timedelta

from dataclasses import asdict

from app import metrics as m


def _d(text: str) -> date:
    return date.fromisoformat(text[:10])


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def load_adherence_weeks(conn: sqlite3.Connection, user_id: int) -> list[tuple[int, int]]:
    rows = conn.execute(
        """SELECT c.checkin_id, c.checkin_date, s.training_schedule
           FROM checkins c JOIN profile_snapshots s ON s.snapshot_id = c.snapshot_id
           WHERE c.user_id = ? ORDER BY c.checkin_date""", (user_id,)).fetchall()
    scheduled: dict[date, int] = {}
    done: dict[date, set] = defaultdict(set)
    for r in rows:
        wk = _week_start(_d(r["checkin_date"]))
        try:
            days = json.loads(r["training_schedule"] or "{}").get("days", [])
        except (ValueError, AttributeError):
            days = []
        scheduled[wk] = len(set(days))  # later check-in in the same week wins
        for w in conn.execute(
                "SELECT DISTINCT session_day FROM workout_logs WHERE checkin_id = ? AND session_day IS NOT NULL",
                (r["checkin_id"],)):
            done[wk].add(w["session_day"])
    return [(scheduled[wk], len(done[wk])) for wk in sorted(scheduled)]


def load_weight_points(conn: sqlite3.Connection, user_id: int) -> list[tuple[date, float]]:
    rows = conn.execute(
        """SELECT COALESCE(c.checkin_date, date(s.created_at)) AS d, s.weight AS w
           FROM profile_snapshots s LEFT JOIN checkins c ON c.snapshot_id = s.snapshot_id
           WHERE s.user_id = ? AND s.weight IS NOT NULL""", (user_id,)).fetchall()
    return [(_d(r["d"]), r["w"]) for r in rows]


def load_sleep_entries(conn: sqlite3.Connection, user_id: int) -> list[tuple[str, str]]:
    rows = conn.execute(
        """SELECT sl.bed_time, sl.wake_time FROM sleep_logs sl JOIN checkins c ON c.checkin_id = sl.checkin_id
           WHERE c.user_id = ? AND sl.bed_time IS NOT NULL AND sl.wake_time IS NOT NULL
           ORDER BY c.checkin_date""", (user_id,)).fetchall()
    return [(r["bed_time"], r["wake_time"]) for r in rows]


def load_strength_sets(conn: sqlite3.Connection, user_id: int) -> dict[str, list]:
    rows = conn.execute(
        """SELECT e.name, c.checkin_date, w.weight_used, w.reps
           FROM workout_logs w JOIN checkins c ON c.checkin_id = w.checkin_id
           JOIN exercises e ON e.exercise_id = w.exercise_id
           WHERE c.user_id = ? AND w.weight_used IS NOT NULL AND w.reps IS NOT NULL""", (user_id,)).fetchall()
    out: dict[str, list] = defaultdict(list)
    for r in rows:
        out[r["name"]].append((_d(r["checkin_date"]), r["weight_used"], r["reps"]))
    return out


def load_latest_profile(conn: sqlite3.Connection, user_id: int):
    """Newest snapshot: the profile as it stands now (snapshots are immutable, so newest wins)."""
    return conn.execute(
        "SELECT * FROM profile_snapshots WHERE user_id = ? ORDER BY created_at DESC, snapshot_id DESC LIMIT 1",
        (user_id,)).fetchone()


def compute_energy(profile, weight_trend: m.MetricResult) -> list[m.MetricResult]:
    """BMR, TDEE, expected loss, muscle range and the loss comparison from the latest profile (CR-2 to CR-7)."""
    p = dict(profile) if profile is not None else {}
    bmr = m.bmr_mifflin(p.get("weight"), p.get("height"), p.get("age"), p.get("sex"))
    tdee = m.tdee_kcal(p.get("weight"), p.get("height"), p.get("age"), p.get("sex"), p.get("activity_level"))
    loss = m.expected_loss_kg_per_week(tdee.value, p.get("weight"), p.get("intake_kcal"), p.get("deficit_level"))
    muscle = m.muscle_gain_range_kg_per_week(p.get("weight"), p.get("training_level"), p.get("sex"))
    return [bmr, tdee, loss, muscle, m.loss_comparison(weight_trend, loss)]

def store_results(conn: sqlite3.Connection, user_id: int, results: list[m.MetricResult], as_of: date) -> dict[str, int]:
    """Write the ok results to the metrics table. Returns {metric_type: metric_id} so a suggestion can cite them."""
    stamp = f"{as_of.isoformat()}T00:00:00.000Z"
    ids: dict[str, int] = {}
    for r in results:
        if r.ok:
            cur = conn.execute("INSERT INTO metrics (user_id, metric_type, value, computed_at) VALUES (?,?,?,?)",
                               (user_id, r.metric_type, r.value, stamp))
            ids[r.metric_type] = cur.lastrowid
    conn.commit()
    return ids




def compute_all(conn: sqlite3.Connection, user_id: int, as_of: date, store: bool = True) -> list[m.MetricResult]:
    results = [
        m.adherence_pct(load_adherence_weeks(conn, user_id)),
        m.weight_trend_kg_per_week(load_weight_points(conn, user_id), as_of),
        m.sleep_consistency_min(load_sleep_entries(conn, user_id)),
    ]
    results += compute_energy(load_latest_profile(conn, user_id), results[1])
    sets = load_strength_sets(conn, user_id)
    if sets:  # report the exercise with the most usable top-set dates
        top = max(sets, key=lambda n: len({d for d, w, r in sets[n] if m.epley_1rm(w, r) is not None}))
        results.append(m.strength_progression_pct_per_week(top, sets[top]))
    if store:
        store_results(conn, user_id, results, as_of)
    return results



def metrics_report(conn: sqlite3.Connection, user_id: int, as_of: str | None = None) -> dict:
    """JSON-ready metrics for one user. Raises LookupError (no such user) or ValueError (bad date).

    Default date is the user's latest check-in, so a demo gives the same numbers every time.
    """
    if conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone() is None:
        raise LookupError("User not found")
    if as_of:
        when = date.fromisoformat(as_of)  # ValueError if malformed
    else:
        latest = conn.execute("SELECT MAX(checkin_date) FROM checkins WHERE user_id = ?", (user_id,)).fetchone()[0]
        when = date.fromisoformat(latest) if latest else date.today()
    results = compute_all(conn, user_id, when, store=False)
    return {"user_id": user_id, "as_of": when.isoformat(), "metrics": [asdict(r) for r in results]}
