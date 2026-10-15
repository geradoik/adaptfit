"""Rule-based suggestions. Pure functions: metrics in, one suggestion out. No database, no AI (FR-12, NFR-7).
 
Each suggestion comes from exactly one rule in RULES. The rule's description and citation are stored with the
suggestion so the "Why this suggestion?" screen can show the numbers and the reason behind it.
 
HONESTY NOTE: the numeric thresholds below (60%, 80%, 1.25x, 0.75x, 45 minutes) are design choices, not findings
from a study. What the studies support is the DIRECTION of each rule. Each citation says which is which. Rule set v2
follows the evidence review "AdaptFit Suggestion Rules: Evidence Review" (15 October 2026).
"""
from __future__ import annotations
 
from dataclasses import dataclass, field
 
from .metrics import MetricResult
 
RULE_SET_VERSION = "v2"
 
LOW_ADHERENCE_PCT = 60.0          # design choice
HIGH_ADHERENCE_PCT = 80.0         # design choice
IRREGULAR_SLEEP_MIN = 45.0        # design choice
MIN_SESSIONS_PER_WEEK = 2         # R3 never suggests fewer than this (Currier 2023: twice a week ranks top for muscle)
 
RULES = {
    "R1": {
        "description": "Too little data for a suggestion yet",
        "citation": "Design rule: metrics need at least 2 weeks of check-ins. Early weight change mixes water and "
                    "glycogen with fat (Egan et al. 2024, Journal of Nutritional Science).",
    },
    "R2": {
        "description": "Weight is falling faster than the plan expects, on two check-ins in a row",
        "citation": "The 1.25x threshold and the two-in-a-row requirement are design choices. Background: a deficit of "
                    "about 500 kcal/day or more impaired lean-mass gain in people lifting (Murphy and Koehler 2022, "
                    "Scand J Med Sci Sports); early loss includes water and glycogen (Egan et al. 2024).",
    },
    "R3": {
        "description": "Fewer than 60% of planned sessions were completed",
        "citation": "The 60% trigger is a design choice. Background: more weekly sets gave more strength (Ralston et "
                    "al. 2017, Sports Medicine); twice-weekly training ranked top for muscle (Currier et al. 2023, "
                    "Br J Sports Med), and once a week gave similar growth when volume was equal (Grgic et al. 2019, "
                    "J Sci Med Sport).",
    },
    "R4": {
        "description": "Bed and wake times vary by more than 45 minutes",
        "citation": "The 45-minute trigger is a design choice. Background: more variable sleep duration (spread above "
                    "60 minutes) and less regular sleep went with more obesity and higher mortality in older adults "
                    "(Kianersi et al. 2025, Int J Obes; Windred et al. 2024, Sleep). Association only, and measured "
                    "differently from AdaptFit's bed and wake spread.",
    },
    "R5": {
        "description": "Weight is changing more slowly than the plan expects",
        "citation": "The 0.75x threshold is a design choice. The calorie-deficit rule behind expected loss "
                    "overestimates loss because energy expenditure adapts (Egan et al. 2024, Journal of Nutritional "
                    "Science).",
    },
    "R6": {
        "description": "Training is consistent and strength is rising",
        "citation": "The 80% trigger is a design choice. Background: adding load or adding repetitions built similar "
                    "strength and muscle in untrained adults (Chaves et al. 2024, Int J Sports Med); training to "
                    "failure was not better for muscle growth (Refalo et al. 2023, Sports Medicine).",
    },
    "R7": {
        "description": "Nothing measured needs changing",
        "citation": "Design rule: no change is suggested when no other rule applies. It only reflects adherence, "
                    "weight, sleep and strength.",
    },
}
 
# How to show each metric to the user: label, window text, and a formatter for the value.
METRIC_DISPLAY = {
    "adherence_pct": ("Adherence", "last 4 weeks", lambda v: f"{v:.0f}%"),
    "weight_trend_kg_per_week": ("Weight trend", "last 2 weeks", lambda v: f"{v:+.2f} kg/week"),
    "sleep_consistency_min": ("Bed and wake time spread", "last 4 check-ins", lambda v: f"{v:.0f} min spread"),
    "loss_vs_expected_ratio": ("Loss versus plan", "measured / expected", lambda v: f"{v:.2f}x the expected loss"),
    "expected_loss_kg_per_week": ("Expected loss", "early-weeks estimate", lambda v: f"{v:.2f} kg/week"),
    "strength_progression_pct_per_week": ("Strength", "top-set trend", lambda v: f"{v:+.1f}% per week"),
}
 
 
def display_for(metric_type: str, value: float) -> dict:
    key = metric_type.split(":")[0]
    label, window, fmt = METRIC_DISPLAY.get(key, (metric_type, "", lambda v: f"{v:.2f}"))
    if ":" in metric_type:
        label = f"{label} ({metric_type.split(':', 1)[1]})"
    return {"metric_type": metric_type, "label": label, "window": window, "value_text": fmt(value)}
 
 
@dataclass(frozen=True)
class Suggestion:
    rule_key: str
    text: str
    metric_types: list = field(default_factory=list)  # which metrics this suggestion is based on
 
 
def _find(results: list[MetricResult], prefix: str) -> MetricResult | None:
    for r in results:
        if r.metric_type == prefix or r.metric_type.startswith(prefix + ":"):
            return r
    return None
 
 
def _faster_than_expected(results: list[MetricResult] | None) -> bool:
    """True when this set of results says weight is falling faster than the plan expects."""
    if not results:
        return False
    ratio = _find(results, "loss_vs_expected_ratio")
    return bool(ratio and ratio.ok and ratio.detail.get("status") == "faster_than_expected")
 
 
def _smaller_plan_text(adherence: MetricResult) -> str:
    """R3 wording. Never suggests fewer than MIN_SESSIONS_PER_WEEK sessions (Currier et al. 2023)."""
    planned = round(adherence.detail["scheduled"] / adherence.detail["weeks_used"])
    start = f"You completed {adherence.value:.0f}% of your planned sessions."
    studies = "Studies find 2 sessions a week still builds strength and muscle when you work hard in each one."
    if planned < MIN_SESSIONS_PER_WEEK:
        return f"{start} Keep your {max(planned, 1)} session a week and aim to complete it; add a second when you can."
    if planned == MIN_SESSIONS_PER_WEEK:
        return (f"{start} For the next two weeks, stay at {planned} sessions a week and aim to complete both. "
                f"{studies}")
    smaller = max(MIN_SESSIONS_PER_WEEK, planned - 1)
    text = f"{start} For the next two weeks, try {smaller} sessions a week."
    if smaller == MIN_SESSIONS_PER_WEEK:
        text += " " + studies
    return text
 
 
def choose_suggestion(results: list[MetricResult], previous_results: list[MetricResult] | None = None) -> Suggestion:
    """Pick ONE suggestion. Rules are checked in priority order; the first that applies wins.
 
    previous_results are the metrics as they stood at the check-in before this one. R2 needs them, because it only
    fires when weight is falling faster than planned on two check-ins in a row (early loss includes water).
    """
    adherence = _find(results, "adherence_pct")
    trend = _find(results, "weight_trend_kg_per_week")
    sleep = _find(results, "sleep_consistency_min")
    ratio = _find(results, "loss_vs_expected_ratio")
    strength = _find(results, "strength_progression_pct_per_week")
 
    # R1: nothing reliable to base advice on.
    if not (adherence and adherence.ok) and not (trend and trend.ok):
        return Suggestion("R1", "Log one more weekly check-in. Your numbers and suggestions appear after two weeks "
                                "of data.", [])
 
    # R2: safety first. Losing faster than planned on two check-ins in a row.
    fast_now = _faster_than_expected(results)
    if fast_now and _faster_than_expected(previous_results):
        return Suggestion("R2", "You are losing weight faster than your plan expects. If this continues, a smaller "
                                "deficit helps keep muscle and makes the loss easier to sustain.",
                          ["weight_trend_kg_per_week", "expected_loss_kg_per_week", "loss_vs_expected_ratio"])
 
    # R3: low adherence.
    if adherence and adherence.ok and adherence.value < LOW_ADHERENCE_PCT:
        return Suggestion("R3", _smaller_plan_text(adherence), ["adherence_pct"])
 
    # R4: irregular sleep.
    if sleep and sleep.ok and sleep.value > IRREGULAR_SLEEP_MIN:
        return Suggestion("R4", f"Your bed and wake times vary by about {sleep.value:.0f} minutes. Large studies link "
                                f"steadier sleep timing with better health. This week, try to keep both within 30 "
                                f"minutes of the same time.", ["sleep_consistency_min"])
 
    # R5: slower than the plan expects.
    if ratio and ratio.ok and ratio.detail.get("status") == "slower_than_expected":
        return Suggestion("R5", "Your weight is changing more slowly than your plan predicts. This is common early "
                                "on, and estimates like this usually run higher than real-world results. Check your "
                                "intake against your plan and give it two more weeks before changing anything.",
                          ["weight_trend_kg_per_week", "expected_loss_kg_per_week", "loss_vs_expected_ratio"])
 
    # R6: consistent and getting stronger.
    if (adherence and adherence.ok and adherence.value >= HIGH_ADHERENCE_PCT
            and strength and strength.ok and strength.value > 0):
        return Suggestion("R6", "Good consistency and your lifts are going up. If your last sets felt manageable, "
                                "add one rep to each set, or the smallest weight increase you have, next week.",
                          ["adherence_pct", strength.metric_type])
 
    used = [t for t, r in (("adherence_pct", adherence), ("weight_trend_kg_per_week", trend)) if r and r.ok]
    text = "Nothing we measure needs changing this week. Keep your current plan."
    if fast_now:
        # One fast check-in is weak evidence (early loss includes water), so R2 waits for a second one.
        text += (" Your weight is dropping a little faster than planned; if the next check-in shows the same, we "
                 "will suggest a change.")
        used += [t for t in ("expected_loss_kg_per_week", "loss_vs_expected_ratio") if t not in used]
    return Suggestion("R7", text, used)
 