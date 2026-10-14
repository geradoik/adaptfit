"""Rule-based suggestions. Pure functions: metrics in, one suggestion out. No database, no AI (FR-12, NFR-7).

Each suggestion comes from exactly one rule in RULES. The rule's description and citation are stored with the
suggestion so the "Why this suggestion?" screen can show the numbers and the reason behind it.

HONESTY NOTE: the thresholds below are design choices, not findings from a study. The citation text says what, if
anything, supports each rule. Source or change them before the final report (docs/metrics.md, section on evidence).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .metrics import MetricResult

RULE_SET_VERSION = "v1"

LOW_ADHERENCE_PCT = 60.0          # design choice
HIGH_ADHERENCE_PCT = 80.0         # design choice
IRREGULAR_SLEEP_MIN = 45.0        # design choice

RULES = {
    "R1": {
        "description": "Too little data for a suggestion yet",
        "citation": "Design rule: metrics need at least 2 weeks of check-ins (docs/metrics.md).",
    },
    "R2": {
        "description": "Weight is falling faster than the plan expects",
        "citation": "Threshold is a design choice (1.25x the expected loss). Background: Hall et al. 2011, The Lancet, "
                    "on how short-term energy-balance estimates behave.",
    },
    "R3": {
        "description": "Fewer than 60% of planned sessions were completed",
        "citation": "Design rule, no study cited yet. Threshold is a design choice.",
    },
    "R4": {
        "description": "Bed and wake times vary by more than 45 minutes",
        "citation": "Threshold is a design choice. Background: Windred et al. 2024, Sleep (an association only; a 2025 "
                    "analysis found the result depends on the software used).",
    },
    "R5": {
        "description": "Weight is changing more slowly than the plan expects",
        "citation": "Threshold is a design choice (below 0.75x the expected loss). Expected loss is an early-weeks "
                    "estimate (Hall et al. 2011).",
    },
    "R6": {
        "description": "Training is consistent and strength is rising",
        "citation": "Design rule, no study cited yet. Threshold is a design choice.",
    },
    "R7": {
        "description": "Everything measured is on track",
        "citation": "Design rule: no change is needed when no other rule applies.",
    },
}

# How to show each metric to the user: label, window text, and a formatter for the value.
METRIC_DISPLAY = {
    "adherence_pct": ("Adherence", "last 4 weeks", lambda v: f"{v:.0f}%"),
    "weight_trend_kg_per_week": ("Weight trend", "last 2 weeks", lambda v: f"{v:+.2f} kg/week"),
    "sleep_consistency_min": ("Sleep consistency", "last 4 check-ins", lambda v: f"{v:.0f} min spread"),
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


def choose_suggestion(results: list[MetricResult]) -> Suggestion:
    """Pick ONE suggestion. Rules are checked in priority order; the first that applies wins."""
    adherence = _find(results, "adherence_pct")
    trend = _find(results, "weight_trend_kg_per_week")
    sleep = _find(results, "sleep_consistency_min")
    ratio = _find(results, "loss_vs_expected_ratio")
    strength = _find(results, "strength_progression_pct_per_week")

    # R1: nothing reliable to base advice on.
    if not (adherence and adherence.ok) and not (trend and trend.ok):
        return Suggestion("R1", "Log one more weekly check-in. Your numbers and suggestions appear after two weeks "
                                "of data.", [])

    # R2: safety first. Losing faster than planned.
    if ratio and ratio.ok and ratio.detail.get("status") == "faster_than_expected":
        return Suggestion("R2", "You are losing weight faster than your plan expects. Consider eating a little more "
                                "this week; steady loss is easier to keep.",
                          ["weight_trend_kg_per_week", "expected_loss_kg_per_week", "loss_vs_expected_ratio"])

    # R3: low adherence.
    if adherence and adherence.ok and adherence.value < LOW_ADHERENCE_PCT:
        per_week = adherence.detail["scheduled"] / adherence.detail["weeks_used"]
        smaller = max(1, round(per_week) - 1)
        return Suggestion("R3", f"You completed {adherence.value:.0f}% of your planned sessions. For the next two "
                                f"weeks, try a smaller plan you can keep: {smaller} "
                                f"session{'s' if smaller != 1 else ''} a week.", ["adherence_pct"])

    # R4: irregular sleep.
    if sleep and sleep.ok and sleep.value > IRREGULAR_SLEEP_MIN:
        return Suggestion("R4", f"Your bed and wake times vary by about {sleep.value:.0f} minutes. This week, try to "
                                f"keep both within 30 minutes of the same time.", ["sleep_consistency_min"])

    # R5: slower than the plan expects.
    if ratio and ratio.ok and ratio.detail.get("status") == "slower_than_expected":
        return Suggestion("R5", "Your weight is changing more slowly than your plan predicts. This is common early "
                                "on. Check your intake against your plan and give it two more weeks before changing "
                                "anything.", ["weight_trend_kg_per_week", "expected_loss_kg_per_week",
                                              "loss_vs_expected_ratio"])

    # R6: consistent and getting stronger.
    if (adherence and adherence.ok and adherence.value >= HIGH_ADHERENCE_PCT
            and strength and strength.ok and strength.value > 0):
        return Suggestion("R6", "Good consistency and your lifts are going up. If your last sets felt manageable, "
                                "add the smallest weight increase you have next week.",
                          ["adherence_pct", strength.metric_type])

    used = [t for t, r in (("adherence_pct", adherence), ("weight_trend_kg_per_week", trend)) if r and r.ok]
    return Suggestion("R7", "You are on track. Keep your current plan this week.", used)
