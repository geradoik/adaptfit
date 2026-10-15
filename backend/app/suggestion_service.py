"""Create and read suggestions, with the traceability links that power "Why this suggestion?" (FR-14, NFR-7).
 
generate_suggestion(): compute metrics -> store them -> pick a rule -> save the suggestion and link it to the
exact metric rows and the rule it came from. latest_suggestion(): read it back with the reasons.
"""
from __future__ import annotations
 
import sqlite3
from datetime import date
 
from . import metrics_service, suggestions
 
DISCLAIMER = "General fitness guidance, not medical advice."
 
 
def _ensure_rule(conn: sqlite3.Connection, rule_key: str) -> tuple[int, dict]:
    rule = suggestions.RULES[rule_key]
    description = f"{rule_key}: {rule['description']}"
    row = conn.execute("SELECT rule_id FROM evidence_rules WHERE description = ? AND version = ?",
                       (description, suggestions.RULE_SET_VERSION)).fetchone()
    if row:
        return row["rule_id"], rule
    rule_id = conn.execute("INSERT INTO evidence_rules (description, citation, version) VALUES (?,?,?)",
                           (description, rule["citation"], suggestions.RULE_SET_VERSION)).lastrowid
    return rule_id, rule
 
 
def _previous_results(conn: sqlite3.Connection, user_id: int, as_of: date) -> list | None:
    """Metrics as they stood at the check-in before as_of, or None if there was no earlier check-in.
 
    Only the weight trend depends on the date, and it ignores weigh-ins after the date, so this is safe to compute
    now. Nothing is stored. R2 uses it to ask: was weight ALSO falling faster than planned last time?
    """
    row = conn.execute("SELECT MAX(checkin_date) FROM checkins WHERE user_id = ? AND checkin_date < ?",
                       (user_id, as_of.isoformat())).fetchone()
    if row[0] is None:
        return None
    return metrics_service.compute_all(conn, user_id, date.fromisoformat(row[0]), store=False)
 
 
def generate_suggestion(conn: sqlite3.Connection, user_id: int, as_of: date | None = None) -> int:
    """Returns the new recommendation_id. Raises LookupError if the user does not exist."""
    if conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone() is None:
        raise LookupError("User not found")
    if as_of is None:
        latest = conn.execute("SELECT MAX(checkin_date) FROM checkins WHERE user_id = ?", (user_id,)).fetchone()[0]
        as_of = date.fromisoformat(latest) if latest else date.today()
 
    results = metrics_service.compute_all(conn, user_id, as_of, store=False)
    metric_ids = metrics_service.store_results(conn, user_id, results, as_of)
    chosen = suggestions.choose_suggestion(results, _previous_results(conn, user_id, as_of))
    try:
        rec_id = conn.execute("INSERT INTO recommendations (user_id, content) VALUES (?, ?)",
                              (user_id, chosen.text)).lastrowid
        for metric_type in chosen.metric_types:
            if metric_type in metric_ids:  # only metrics that were actually computed and stored
                conn.execute("INSERT OR IGNORE INTO recommendation_metrics (recommendation_id, metric_id) VALUES (?,?)",
                             (rec_id, metric_ids[metric_type]))
        rule_id, _ = _ensure_rule(conn, chosen.rule_key)
        conn.execute("INSERT INTO recommendation_rules (recommendation_id, rule_id) VALUES (?,?)", (rec_id, rule_id))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return rec_id
 
 
def latest_suggestion(conn: sqlite3.Connection, user_id: int) -> dict | None:
    """The newest suggestion with the metrics and rule behind it, or None if there is none yet."""
    rec = conn.execute("SELECT * FROM recommendations WHERE user_id = ? ORDER BY generated_at DESC, "
                       "recommendation_id DESC LIMIT 1", (user_id,)).fetchone()
    if rec is None:
        return None
    based_on = [
        suggestions.display_for(r["metric_type"], r["value"])
        for r in conn.execute(
            """SELECT m.metric_type, m.value FROM recommendation_metrics rm
               JOIN metrics m ON m.metric_id = rm.metric_id
               WHERE rm.recommendation_id = ? ORDER BY m.metric_id""", (rec["recommendation_id"],))
    ]
    evidence = [
        {"description": r["description"], "citation": r["citation"], "version": r["version"]}
        for r in conn.execute(
            """SELECT e.description, e.citation, e.version FROM recommendation_rules rr
               JOIN evidence_rules e ON e.rule_id = rr.rule_id
               WHERE rr.recommendation_id = ?""", (rec["recommendation_id"],))
    ]
    return {
        "recommendation_id": rec["recommendation_id"],
        "generated_at": rec["generated_at"],
        "text": rec["content"],
        "tags": ["Rules"] + (["Estimate"] if any(b["metric_type"] == "expected_loss_kg_per_week" for b in based_on) else []),
        "based_on": based_on,
        "evidence": evidence,
        "how_written": "Rule-based suggestion. AI explanations are off.",
        "disclaimer": DISCLAIMER,
    }
 