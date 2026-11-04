"""Onboarding: validate the answers and create the user plus their baseline profile snapshot (FR-3, FR-4).
There is no login yet (not a priority atm), so each onboarding creates an anonymous prototype user.
"""
from __future__ import annotations

import json
import sqlite3
import uuid

DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
SEXES = ("male", "female")
ACTIVITY_LEVELS = ("sedentary", "light", "moderate", "very_active", "extra_active")
TRAINING_LEVELS = ("novice", "intermediate", "advanced")
GOALS = ("build_muscle", "get_stronger", "lose_fat", "stay_consistent")
DIET_PATTERNS = ("regular_meals", "irregular", "not_sure")
DEFICIT_LEVELS = ("small", "moderate", "large")

def _number(data: dict, key: str, low: float, high: float, errors: list, label: str, required: bool = True):
    value = data.get(key)
    if value in (None, ""):
        if required:
            errors.append(f"{label} is required")
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        errors.append(f"{label} must be a number")
        return None
    if not (low <= number <= high):
        errors.append(f"{label} must be between {low:g} and {high:g}")
        return None
    return number

def _choice(data: dict, key: str, allowed: tuple, errors: list, label: str, required: bool = True):
    value = data.get(key)
    if value in (None, ""):
        if required:
            errors.append(f"{label} is required")
        return None
    if value not in allowed:
        errors.append(f"{label} must be one of: {', '.join(allowed)}")
        return None
    return value


def validate_onboarding(data: dict) -> tuple[dict, list[str]]:
    """Return (clean values, list of error messages). An empty error list means the data is usable."""
    errors: list[str] = []
    clean: dict = {}
    clean["weight"] = _number(data, "weight", 25, 400, errors, "Weight (kg)")
    clean["height"] = _number(data, "height", 100, 250, errors, "Height (cm)")
    age = _number(data, "age", 16, 100, errors, "Age")
    clean["age"] = int(age) if age is not None else None
    clean["sex"] = _choice(data, "sex", SEXES, errors, "Sex")
    clean["activity_level"] = _choice(data, "activity_level", ACTIVITY_LEVELS, errors, "Activity level")
    clean["training_level"] = _choice(data, "training_level", TRAINING_LEVELS, errors, "Training level")
    clean["goal"] = _choice(data, "goal", GOALS, errors, "Goal")
    clean["diet_pattern"] = _choice(data, "diet_pattern", DIET_PATTERNS, errors, "Eating pattern", required=False)
    # Calorie input is OPTIONAL (change request CR-3).
    clean["deficit_level"] = _choice(data, "deficit_level", DEFICIT_LEVELS, errors, "Deficit level", required=False)
    intake = _number(data, "intake_kcal", 800, 6000, errors, "Daily calories", required=False)
    clean["intake_kcal"] = int(intake) if intake is not None else None

    days = data.get("training_days")
    if not isinstance(days, list) or not days:
        errors.append("Pick at least one training day")
    elif any(d not in DAYS for d in days):
        errors.append("Training days must be mon, tue, wed, thu, fri, sat or sun")
    else:
        clean["training_days"] = [d for d in DAYS if d in days]  # sorted Monday to Sunday, no duplicates

    # Sleep times are optional here; if given they must look like HH:MM.
    for key, label in (("bed_time", "Bedtime"), ("wake_time", "Wake time")):
        value = data.get(key)
        if value in (None, ""):
            clean[key] = None
            continue
        try:
            hh, mm = str(value).split(":")
            assert 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59
            clean[key] = f"{int(hh):02d}:{int(mm):02d}"
        except (ValueError, AssertionError):
            errors.append(f"{label} must look like 23:00")
    return clean, errors

def save_onboarding(conn: sqlite3.Connection, data: dict) -> int:
    """Create the user and the baseline snapshot in one transaction. Returns user_id or ValueError."""
    clean, errors = validate_onboarding(data)
    if errors:
        raise ValueError("; ".join(errors))
    sleep_pattern = f"{clean['bed_time']}-{clean['wake_time']}" if clean["bed_time"] and clean["wake_time"] else None
    try:
        email = f"user-{uuid.uuid4().hex[:12]}@prototype.adaptfit"  # placeholder until login exists
        user_id = conn.execute("INSERT INTO users (email, password_hash) VALUES (?, 'prototype-no-login')",
                               (email,)).lastrowid
        conn.execute(
            """INSERT INTO profile_snapshots (user_id, weight, height, sleep_pattern, training_schedule, goal,
               diet_pattern, age, sex, activity_level, training_level, deficit_level, intake_kcal)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, clean["weight"], clean["height"], sleep_pattern,
             json.dumps({"days": clean["training_days"]}), clean["goal"], clean["diet_pattern"], clean["age"],
             clean["sex"], clean["activity_level"], clean["training_level"], clean["deficit_level"],
             clean["intake_kcal"]))
        conn.commit()
        return user_id
    except Exception:
        conn.rollback()
        raise

def load_profile(conn: sqlite3.Connection, user_id: int) -> dict | None:
    """The user's newest snapshot as a plain dict, with the schedule unpacked to a list of days."""
    row = conn.execute(
        "SELECT * FROM profile_snapshots WHERE user_id = ? ORDER BY created_at DESC, snapshot_id DESC LIMIT 1",
        (user_id,)).fetchone()
    if row is None:
        return None
    profile = dict(row)
    try:
        profile["training_days"] = json.loads(profile.pop("training_schedule") or "{}").get("days", [])
    except ValueError:
        profile["training_days"] = []
    return profile
