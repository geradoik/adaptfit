"""Deterministic trend engine: pure functions, no database, no network, no LLM (FR-9, NFR-7).

Every function returns a rsult. When there is too little data the result has
status "not_enough_data".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from statistics import mean, stdev

OK = "ok"
NOT_ENOUGH = "not_enough_data"

ADHERENCE_WEEKS = 4
ADHERENCE_MIN_WEEKS = 2
WEIGHT_WINDOW_DAYS = 14
SLEEP_WINDOW = 4
SLEEP_MIN_ENTRIES = 3
STRENGTH_MAX_REPS = 10
STRENGTH_MIN_SPAN_DAYS = 7


@dataclass(frozen=True)
class MetricResult:
    metric_type: str
    status: str
    value: float | None = None
    unit: str = ""
    detail: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == OK


def _not_enough(metric_type: str, unit: str, **detail) -> MetricResult:
    return MetricResult(metric_type, NOT_ENOUGH, None, unit, detail)


# --- adherence -------------------------------------------------------------
def adherence_pct(weeks: list[tuple[int, int]]) -> MetricResult:
    """weeks: (scheduled_sessions, completed_distinct_sessions) per logged week, oldest first.

    Uses the last 4 weeks. Completed is capped at scheduled per week so extra sessions do not
    hide missed ones. Weeks with nothing scheduled are a chop. Needs at least 2 usable weeks.
    """
    usable = [(s, min(c, s)) for s, c in weeks if s > 0][-ADHERENCE_WEEKS:]
    if len(usable) < ADHERENCE_MIN_WEEKS:
        return _not_enough("adherence_pct", "%", weeks_used=len(usable), weeks_needed=ADHERENCE_MIN_WEEKS)
    scheduled = sum(s for s, _ in usable)
    completed = sum(c for _, c in usable)
    return MetricResult("adherence_pct", OK, 100.0 * completed / scheduled, "%",
                        {"weeks_used": len(usable), "completed": completed, "scheduled": scheduled})


# --- weight trend ----------------------------------------------------------
def weight_trend_kg_per_week(points: list[tuple[date, float]], as_of: date) -> MetricResult:
    """Mean weight in (T-14, T] minus mean weight in (T-28, T-14], divided by 2 weeks.

    Negative means weight is falling. Needs at least one point in each window.
    """
    recent_from = as_of - timedelta(days=WEIGHT_WINDOW_DAYS)
    older_from = as_of - timedelta(days=2 * WEIGHT_WINDOW_DAYS)
    recent = [w for d, w in points if recent_from < d <= as_of]
    older = [w for d, w in points if older_from < d <= recent_from]
    if not recent or not older:
        return _not_enough("weight_trend_kg_per_week", "kg/week",
                           recent_points=len(recent), older_points=len(older))
    value = (mean(recent) - mean(older)) / 2.0
    return MetricResult("weight_trend_kg_per_week", OK, value, "kg/week",
                        {"recent_mean": mean(recent), "older_mean": mean(older),
                         "recent_points": len(recent), "older_points": len(older)})


# --- sleep consistency -----------------------------------------------------
def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def bed_minutes_since_18(hhmm: str) -> int:
    """Minutes since 18:00, so 23:30 -> 330 and 00:30 -> 390 (no midnight wrap-around problem)."""
    return (_minutes(hhmm) - 18 * 60) % 1440


def sleep_consistency_min(entries: list[tuple[str, str]]) -> MetricResult:
    """entries: (bed 'HH:MM', wake 'HH:MM') for the most recent check-ins that have both, oldest first.

    Value = average of the sample SD of bed times and the sample SD of wake times, in minutes.
    Lower is more consistent. Needs at least 3 entries; uses the last 4.
    """
    recent = entries[-SLEEP_WINDOW:]
    if len(recent) < SLEEP_MIN_ENTRIES:
        return _not_enough("sleep_consistency_min", "min", entries=len(recent), entries_needed=SLEEP_MIN_ENTRIES)
    bed_sd = stdev([bed_minutes_since_18(b) for b, _ in recent])
    wake_sd = stdev([_minutes(w) for _, w in recent])
    return MetricResult("sleep_consistency_min", OK, (bed_sd + wake_sd) / 2.0, "min",
                        {"bed_sd": bed_sd, "wake_sd": wake_sd, "entries": len(recent)})


# --- strength --------------------------------------------------------------
def epley_1rm(weight: float, reps: int) -> float | None:
    """Epley estimate: w * (1 + reps/30). Only trusted for 1-10 reps and a positive load."""
    if weight is None or reps is None or weight <= 0 or reps < 1 or reps > STRENGTH_MAX_REPS:
        return None
    return weight * (1 + reps / 30.0)


def strength_progression_pct_per_week(exercise: str, sets: list[tuple[date, float, int]]) -> MetricResult:
    """sets: (date, weight, reps). Best estimated 1RM per date; % change first -> last, per week.

    Needs two distinct dates at least 7 days apart. Sets outside 1-10 reps are ignored.
    """
    metric_type = f"strength_progression_pct_per_week:{exercise}"
    best: dict[date, float] = {}
    for d, w, r in sets:
        e = epley_1rm(w, r)
        if e is not None and e > best.get(d, 0.0):
            best[d] = e
    days = sorted(best)
    if len(days) < 2 or (days[-1] - days[0]).days < STRENGTH_MIN_SPAN_DAYS:
        return _not_enough(metric_type, "%/week", usable_dates=len(days))
    first, last = best[days[0]], best[days[-1]]
    weeks = (days[-1] - days[0]).days / 7.0
    return MetricResult(metric_type, OK, 100.0 * (last - first) / first / weeks, "%/week",
                        {"first_e1rm": first, "last_e1rm": last, "weeks": weeks})


# --- energy and body-composition estimates (changing requirements CR-2 to CR-5, CR-7) ----------
ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "very_active": 1.725,
    "extra_active": 1.9,
}
DEFICIT_KCAL = {"small": 250, "moderate": 500, "large": 750}
KCAL_PER_KG_FAT = 7700.0           # conventional; an early-weeks upper bound (Hall et al. 2011)
MAX_LOSS_FRACTION_PER_WEEK = 0.01  # cap: 1% of body weight per week
BMR_RANGE = 0.10                   # show +/-10%: individual error of predictive equations
# Weekly muscle-gain rate as a fraction of body weight, by training level. PRACTITIONER HEURISTIC, not a
# peer-reviewed table (see docs/metrics.md section 4). Women use half.
MUSCLE_RATE_PER_WEEK = {
    "novice": (0.0023, 0.0035),
    "intermediate": (0.0012, 0.0023),
    "advanced": (0.0006, 0.0012),
}
ON_TRACK_LOW, ON_TRACK_HIGH = 0.75, 1.25  # proposed status bands (design choice, not from a study)


def bmr_mifflin(weight_kg, height_cm, age, sex) -> MetricResult:
    """Mifflin-St Jeor resting energy (kcal/day). Needs all four inputs."""
    need = {"weight": weight_kg, "height": height_cm, "age": age, "sex": sex}
    missing = [k for k, v in need.items() if v is None]
    if missing or sex not in ("male", "female"):
        return _not_enough("bmr_kcal", "kcal/day", missing=missing or ["sex"])
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + (5 if sex == "male" else -161)
    return MetricResult("bmr_kcal", OK, bmr, "kcal/day",
                        {"low": bmr * (1 - BMR_RANGE), "high": bmr * (1 + BMR_RANGE)})


def tdee_kcal(weight_kg, height_cm, age, sex, activity_level) -> MetricResult:
    """BMR x activity factor, with a +/-10% range."""
    bmr = bmr_mifflin(weight_kg, height_cm, age, sex)
    factor = ACTIVITY_FACTORS.get(activity_level)
    if not bmr.ok or factor is None:
        return _not_enough("tdee_kcal", "kcal/day", missing=["activity_level"] if factor is None else [])
    tdee = bmr.value * factor
    return MetricResult("tdee_kcal", OK, tdee, "kcal/day",
                        {"bmr": bmr.value, "activity_factor": factor,
                         "low": tdee * (1 - BMR_RANGE), "high": tdee * (1 + BMR_RANGE)})


def expected_loss_kg_per_week(tdee, weight_kg, intake_kcal=None, deficit_level=None) -> MetricResult:
    """Expected loss from a calorie deficit, capped at 1% of body weight per week (CR-3, CR-4).

    Calorie input is OPTIONAL: an explicit intake wins, else a deficit level, else not_enough_data.
    A deficit of zero or less gives 0.0 (no loss expected), never a negative loss.
    """
    if tdee is None or weight_kg is None:
        return _not_enough("expected_loss_kg_per_week", "kg/week", missing=["tdee"])
    if intake_kcal is not None:
        deficit = tdee - intake_kcal
    elif deficit_level in DEFICIT_KCAL:
        deficit = DEFICIT_KCAL[deficit_level]
    else:
        return _not_enough("expected_loss_kg_per_week", "kg/week", missing=["intake_kcal or deficit_level"])
    raw = max(deficit, 0) * 7 / KCAL_PER_KG_FAT
    cap = MAX_LOSS_FRACTION_PER_WEEK * weight_kg
    return MetricResult("expected_loss_kg_per_week", OK, min(raw, cap), "kg/week",
                        {"deficit_kcal": deficit, "uncapped": raw, "cap": cap, "capped": raw > cap,
                         "label": "early-weeks estimate"})


def muscle_gain_range_kg_per_week(weight_kg, training_level, sex) -> MetricResult:
    """Realistic muscle-gain range (low, high) in kg/week. Heuristic, labelled as such (CR-5)."""
    rates = MUSCLE_RATE_PER_WEEK.get(training_level)
    if weight_kg is None or rates is None or sex not in ("male", "female"):
        return _not_enough("muscle_gain_kg_per_week", "kg/week")
    scale = 1.0 if sex == "male" else 0.5
    low, high = weight_kg * rates[0] * scale, weight_kg * rates[1] * scale
    return MetricResult("muscle_gain_kg_per_week", OK, (low + high) / 2, "kg/week",
                        {"low": low, "high": high, "label": "heuristic"})


def loss_comparison(weight_trend: MetricResult, expected: MetricResult) -> MetricResult:
    """Q = measured weight change / -expected loss (CR-7). Bands are a proposed design choice."""
    metric_type = "loss_vs_expected_ratio"
    if not weight_trend.ok or not expected.ok or expected.value <= 0:
        return _not_enough(metric_type, "ratio")
    ratio = weight_trend.value / -expected.value
    if ratio < ON_TRACK_LOW:
        status = "slower_than_expected"
    elif ratio <= ON_TRACK_HIGH:
        status = "on_track"
    else:
        status = "faster_than_expected"  # the app should flag this for safety
    return MetricResult(metric_type, OK, ratio, "ratio", {"status": status})
