"""Weight projection: "how much weight will I lose in N weeks?" answered by CODE, never by the AI (FR-9, NFR-7).
 
The AI only puts these numbers into words. Pure functions: numbers in, a plain dict out, no database.
 
Two weekly rates can exist:
  * measured  = the weight trend from real check-ins (kg/week, negative = losing)
  * planned   = the expected loss from the calorie deficit (kg/week, positive = losing; an early-weeks ESTIMATE)
The answer is always a RANGE, never one number, because both rates are uncertain.
"""
from __future__ import annotations
 
MIN_WEEKS, MAX_WEEKS = 1, 12
SINGLE_SOURCE_SPREAD = 0.25   # design choice: with only the measured trend, allow +/-25% around it
PLAN_ONLY_LOW_FRACTION = 0.5  # design choice: a plan-only estimate usually runs high, so the low end is half of it
 
 
def project_weight(current_kg, trend_kg_per_week, expected_loss_kg_per_week, weeks: int) -> dict:
    """Range of weight change after `weeks` weeks.
 
    Example: project_weight(72.3, -0.4, 0.45, 4)
      -> change between -1.8 and -1.6 kg, weight between 70.5 and 70.7 kg, basis "both".
    Missing inputs are None. With neither rate the status is "not_enough_data" (never a guess).
    """
    if not isinstance(weeks, int) or not MIN_WEEKS <= weeks <= MAX_WEEKS:
        raise ValueError(f"weeks must be a whole number from {MIN_WEEKS} to {MAX_WEEKS}")
    if current_kg is None:
        return {"status": "not_enough_data", "weeks": weeks, "reason": "no current weight"}
 
    measured = trend_kg_per_week            # kg per week, negative means losing
    planned = -expected_loss_kg_per_week if expected_loss_kg_per_week is not None else None
 
    if measured is not None and planned is not None:
        basis = "both"
        ends = (measured * weeks, planned * weeks)
    elif measured is not None:
        basis = "measured"
        ends = (measured * weeks * (1 - SINGLE_SOURCE_SPREAD), measured * weeks * (1 + SINGLE_SOURCE_SPREAD))
    elif planned is not None:
        basis = "plan"
        ends = (planned * weeks * PLAN_ONLY_LOW_FRACTION, planned * weeks)
    else:
        return {"status": "not_enough_data", "weeks": weeks, "reason": "no weight trend and no calorie plan"}
 
    low, high = min(ends), max(ends)       # low = biggest drop, high = smallest drop (or a gain)
    return {"status": "ok", "weeks": weeks, "basis": basis, "estimate": True,
            "change_low_kg": round(low, 1), "change_high_kg": round(high, 1),
            "weight_low_kg": round(current_kg + low, 1), "weight_high_kg": round(current_kg + high, 1)}
 
 
def describe(projection: dict) -> str:
    """One plain sentence for a projection dict, used by the rules fallback (no AI involved).
 
    Example: "In 4 weeks your weight is likely to change by about -1.8 to -1.6 kg (an estimate, not a promise)."
    """
    if projection.get("status") != "ok":
        return "There is not enough data yet for a weight projection."
    return (f"In {projection['weeks']} weeks your weight is likely to change by about "
            f"{projection['change_low_kg']:+.1f} to {projection['change_high_kg']:+.1f} kg "
            f"(an estimate, not a promise).")
