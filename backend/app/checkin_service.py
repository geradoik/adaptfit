from datetime import date
from .onboarding_service import DAYS


class DuplicateCheckin(ValueError):
    """The user already has a check-in on that date."""


GENERAL_SESSION = "Session (general)"  # placeholder exercise used when a session is done but no lift is logged
SNAPSHOT_COPY_COLUMNS = ("height", "sleep_pattern", "training_schedule", "goal", "diet_pattern", "age", "sex",
                         "activity_level", "training_level", "deficit_level", "intake_kcal")


def list_exercises(conn: sqlite3.Connection) -> list[dict]:
    """Exercise menu for the lifts picker. The placeholder 'general' exercise is hidden."""
    rows = conn.execute(
        "SELECT exercise_id, name, muscle_group FROM exercises WHERE muscle_group != 'general' "
        "ORDER BY muscle_group, name").fetchall()
    return [dict(r) for r in rows]


def _time(value, label: str, errors: list):
    try:
        hh, mm = str(value).split(":")
        assert 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59
        return f"{int(hh):02d}:{int(mm):02d}"
    except (ValueError, AssertionError):
        errors.append(f"{label} must look like 23:00")
        return None


def validate_checkin(data: dict, today: date) -> tuple[dict, list[str]]:
    errors: list[str] = []
    clean: dict = {}

    raw_date = data.get("checkin_date") or today.isoformat()
    try:
        when = date.fromisoformat(str(raw_date))
        if when > today:
            errors.append("Check-in date cannot be in the future")
        clean["checkin_date"] = when.isoformat()
    except ValueError:
        errors.append("Check-in date must look like 2026-10-12")

    weight = data.get("weight")
    if weight in (None, ""):
        clean["weight"] = None  # keep last week's weight
    else:
        try:
            clean["weight"] = float(weight)
            if not 25 <= clean["weight"] <= 400:
                errors.append("Weight must be between 25 and 400 kg")
        except (TypeError, ValueError):
            errors.append("Weight must be a number")

    done = data.get("done_days") or []
    if not isinstance(done, list) or any(d not in DAYS for d in done):
        errors.append("Sessions done must be days like mon, wed, fri")
        done = []
    clean["done_days"] = [d for d in DAYS if d in done]

    clean["lifts"] = []
    lifts = data.get("lifts") or []
    if not isinstance(lifts, list) or len(lifts) > 3:
        errors.append("Log at most three lifts (top set only)")
        lifts = []
    for i, lift in enumerate(lifts, start=1):
        try:
            item = {
                "exercise_id": int(lift["exercise_id"]),
                "weight_used": float(lift["weight_used"]),
                "reps": int(lift["reps"]),
                "sets": int(lift["sets"]) if lift.get("sets") not in (None, "") else None,
                "session_day": lift.get("session_day") if lift.get("session_day") in DAYS else None,
            }
            if not (0 <= item["weight_used"] <= 500) or not (1 <= item["reps"] <= 100):
                raise ValueError
            clean["lifts"].append(item)
        except (KeyError, TypeError, ValueError):
            errors.append(f"Lift {i} needs an exercise, a weight (0-500 kg) and reps (1-100)")

    sleep = data.get("sleep")
    clean["sleep"] = None
    if sleep and (sleep.get("bed_time") or sleep.get("wake_time")):
        if not (sleep.get("bed_time") and sleep.get("wake_time")):
            errors.append("Give both bedtime and wake time, or leave sleep as 'same as usual'")
        else:
            bed = _time(sleep["bed_time"], "Bedtime", errors)
            wake = _time(sleep["wake_time"], "Wake time", errors)
            if bed and wake:
                clean["sleep"] = {"bed_time": bed, "wake_time": wake}

    protein = data.get("protein_target_met")
    if protein not in (None, True, False):
        errors.append("Protein answer must be yes, no or skipped")
    clean["protein_target_met"] = protein
    return clean, errors


def save_checkin(conn: sqlite3.Connection, user_id: int, data: dict, today: date | None = None) -> dict:
    """Save one check-in. Raises LookupError (no such user or profile) or ValueError (bad data, duplicate date)."""
    today = today or date.today()
    if conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone() is None:
        raise LookupError("User not found")
    previous = conn.execute(
        "SELECT * FROM profile_snapshots WHERE user_id = ? ORDER BY created_at DESC, snapshot_id DESC LIMIT 1",
        (user_id,)).fetchone()
    if previous is None:
        raise LookupError("Finish onboarding first")

    clean, errors = validate_checkin(data, today)
    if errors:
        raise ValueError("; ".join(errors))
    if conn.execute("SELECT 1 FROM checkins WHERE user_id = ? AND checkin_date = ?",
                    (user_id, clean["checkin_date"])).fetchone():
        raise DuplicateCheckin("You already checked in on that date")

    general = conn.execute("SELECT exercise_id FROM exercises WHERE name = ?", (GENERAL_SESSION,)).fetchone()
    if general is None:
        raise LookupError("Exercise list is missing the placeholder session; run the app once to seed it")

    weight = clean["weight"] if clean["weight"] is not None else previous["weight"]
    try:
        columns = ", ".join(SNAPSHOT_COPY_COLUMNS)
        marks = ", ".join("?" for _ in SNAPSHOT_COPY_COLUMNS)
        snapshot_id = conn.execute(
            f"INSERT INTO profile_snapshots (user_id, weight, {columns}) VALUES (?, ?, {marks})",
            (user_id, weight, *[previous[c] for c in SNAPSHOT_COPY_COLUMNS])).lastrowid
        checkin_id = conn.execute(
            "INSERT INTO checkins (user_id, snapshot_id, checkin_date) VALUES (?, ?, ?)",
            (user_id, snapshot_id, clean["checkin_date"])).lastrowid

        done = clean["done_days"]
        days_with_lift = set()
        for lift in clean["lifts"]:
            day = lift["session_day"] if lift["session_day"] in done else (done[0] if done else None)
            days_with_lift.add(day)
            conn.execute(
                "INSERT INTO workout_logs (checkin_id, exercise_id, session_day, sets, reps, weight_used) "
                "VALUES (?,?,?,?,?,?)",
                (checkin_id, lift["exercise_id"], day, lift["sets"], lift["reps"], lift["weight_used"]))
        for day in done:
            if day not in days_with_lift:  # a session was done, but no lift was logged for it
                conn.execute("INSERT INTO workout_logs (checkin_id, exercise_id, session_day) VALUES (?,?,?)",
                             (checkin_id, general["exercise_id"], day))
        if clean["sleep"]:
            conn.execute("INSERT INTO sleep_logs (checkin_id, bed_time, wake_time) VALUES (?,?,?)",
                         (checkin_id, clean["sleep"]["bed_time"], clean["sleep"]["wake_time"]))
        if clean["protein_target_met"] is not None:
            conn.execute("INSERT INTO nutrition_logs (checkin_id, protein_target_met) VALUES (?,?)",
                         (checkin_id, 1 if clean["protein_target_met"] else 0))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"checkin_id": checkin_id, "snapshot_id": snapshot_id, "checkin_date": clean["checkin_date"]}
