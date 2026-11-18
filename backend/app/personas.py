"""Simulated personas (requirement P-1). Every number is invented, no real person's data.
 
Each persona is a profile plus a week-by-week behaviour. The behaviour is fixed (no randomness), so the evaluation
gives the same table every time. run_persona() feeds the weeks through the SAME services the real app uses.
"""
from __future__ import annotations
 
import sqlite3
from datetime import date, timedelta
 
from . import ask_service, checkin_service, onboarding_service, suggestion_service
from .metrics_service import compute_all
 
START = date(2026, 7, 6)         # a Monday; week n is START + 7*(n-1) days
WEEKS = 12
CHECKPOINTS = (1, 6, 12)
QUESTION = "What should I focus on this week?"
 
BASE = {"height": 175, "age": 21, "sex": "male", "activity_level": "moderate", "training_level": "novice",
        "goal": "lose_fat", "deficit_level": "moderate", "training_days": ["mon", "wed", "fri"]}
ALL_DAYS = ("mon", "wed", "fri")
 
 
def _steady_sleep(week):          # same bed and wake time every week
    return "23:00", "06:30"
 
 
def _wobbly_sleep(week):          # bed time jumps between 22:00 and 01:00, wake time between 06:00 and 08:30
    return ("22:00", "06:00") if week % 2 else ("01:00", "08:30")
 
 
# name -> profile, weight(week), done_days(week), sleep(week), squat(week), expected rule at week 12, why
PERSONAS = {
    "steady_lifter": {
        "profile": {**BASE, "weight": 74.4},
        "weight": lambda w: round(74.4 - 0.4 * (w - 1), 1),          # loses 0.4 kg a week: close to the 0.45 plan
        "done": lambda w: ALL_DAYS,                                  # never misses a session
        "sleep": _steady_sleep,
        "squat": lambda w: (50 + 2.5 * (w - 1), 8),                  # adds 2.5 kg every week
        "expected": "R6", "why": "Consistent and getting stronger.",
    },
    "skipper": {
        "profile": {**BASE, "weight": 80.0},
        "weight": lambda w: round(80.0 - 0.1 * (w - 1), 1),
        "done": lambda w: ("mon",),                                  # 1 of 3 sessions
        "sleep": _steady_sleep,
        "squat": lambda w: (60, 8),
        "expected": "R3", "why": "Adherence is 33%, below the 60% trigger.",
    },
    "crash_dieter": {
        "profile": {**BASE, "weight": 90.0, "deficit_level": "small"},
        "weight": lambda w: round(90.0 - 1.5 * (w - 1), 1),          # loses 1.5 kg a week against a 0.2 kg plan
        "done": lambda w: ALL_DAYS,
        "sleep": _steady_sleep,
        "squat": lambda w: (60, 8),
        "expected": "R2", "why": "Losing much faster than planned on two check-ins in a row.",
    },
    "night_owl": {
        "profile": {**BASE, "weight": 74.4},
        "weight": lambda w: round(74.4 - 0.4 * (w - 1), 1),
        "done": lambda w: ALL_DAYS,
        "sleep": _wobbly_sleep,
        "squat": lambda w: (60, 8),                                   # strength flat, so R6 cannot fire
        "expected": "R4", "why": "Bed and wake times vary by far more than 45 minutes.",
    },
    "plateau": {
        "profile": {**BASE, "weight": 85.0},
        "weight": lambda w: 85.0,                                    # weight does not move at all
        "done": lambda w: ALL_DAYS,
        "sleep": _steady_sleep,
        "squat": lambda w: (60, 8),
        "expected": "R5", "why": "Weight is not changing although the plan expects a loss.",
    },
}
 
 
def _rule_key(conn: sqlite3.Connection, user_id: int) -> str:
    """The rule behind the newest weekly suggestion, e.g. 'R6'."""
    evidence = suggestion_service.latest_suggestion(conn, user_id)["evidence"]
    return evidence[0]["description"].split(":")[0]
 
 
def run_persona(conn: sqlite3.Connection, name: str, client=None, checkpoints=CHECKPOINTS) -> list[dict]:
    """Run one persona through 12 weekly check-ins and record what the system said at the checkpoints.
 
    One row per checkpoint: week, date, rule, suggestion text, key metrics and, when a client is given, the AI's
    answer to QUESTION. Rows are also saved in simulation_runs, linked to the persona, so reports can find them.
    """
    spec = PERSONAS[name]
    user_id = onboarding_service.save_onboarding(conn, spec["profile"])
    conn.execute("UPDATE users SET email = ? WHERE user_id = ?", (f"persona-{name}@sim.local", user_id))  # D-4
    conn.execute("INSERT OR IGNORE INTO personas (name, config_description) VALUES (?, ?)", (name, spec["why"]))
    persona_id = conn.execute("SELECT persona_id FROM personas WHERE name = ?", (name,)).fetchone()[0]
    squat = conn.execute("SELECT exercise_id FROM exercises WHERE name = 'Squat'").fetchone()[0]
    conn.commit()
 
    rows = []
    for week in range(1, WEEKS + 1):
        day = START + timedelta(days=7 * (week - 1))
        done = list(spec["done"](week))
        bed, wake = spec["sleep"](week)
        weight, reps = spec["squat"](week)
        checkin_service.save_checkin(conn, user_id, {
            "checkin_date": day.isoformat(), "weight": spec["weight"](week), "done_days": done,
            "sleep": {"bed_time": bed, "wake_time": wake}, "protein_target_met": True,
            "lifts": [{"exercise_id": squat, "weight_used": weight, "reps": reps, "sets": 3,
                       "session_day": done[0]}] if done else []}, today=day)
        rec_id = suggestion_service.generate_suggestion(conn, user_id, day)
        if week not in checkpoints:
            continue
        conn.execute("INSERT INTO simulation_runs (persona_id, recommendation_id, timepoint_label) VALUES (?,?,?)",
                     (persona_id, rec_id, f"week_{week}"))
        conn.commit()
        metrics = {r.metric_type.split(":")[0]: round(r.value, 2) for r in compute_all(conn, user_id, day, store=False)
                   if r.ok}
        row = {"persona": name, "week": week, "date": day.isoformat(), "rule": _rule_key(conn, user_id),
               "suggestion": suggestion_service.latest_suggestion(conn, user_id)["text"],
               "adherence": metrics.get("adherence_pct"), "trend": metrics.get("weight_trend_kg_per_week"),
               "sleep_spread": metrics.get("sleep_consistency_min")}
        if client is not None:
            answer = ask_service.ask(conn, user_id, QUESTION, True, client, today=day)
            row["ai_source"], row["ai_answer"] = answer["generated_by"], answer["answer"]
        rows.append(row)
    return rows
