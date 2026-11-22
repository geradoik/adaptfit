from __future__ import annotations
 
import sqlite3
from datetime import date
 
from . import (llm_context, llm_guard, metrics_service, projection, suggestion_service, suggestions)
from .llm_client import LLMUnavailable
 
REASONS = {
    "no_consent": "AI answers are off. Turn them on in Privacy settings to ask free questions.",
    "no_key": "The AI service is not set up on this server.",
    "unavailable": "The AI service is not available right now.",
    "guard": "The AI's reply did not pass the safety checks, so it was not shown.",
}
 
 
def _as_of(conn: sqlite3.Connection, user_id: int, today: date | None) -> date:
    latest = conn.execute("SELECT MAX(checkin_date) FROM checkins WHERE user_id = ?", (user_id,)).fetchone()[0]
    return date.fromisoformat(latest) if latest else (today or date.today())
 
 
def _fallback_text(conn: sqlite3.Connection, user_id: int, context: dict, reason: str) -> tuple[str, int | None]:
    """Rules-only answer: this week's suggestion plus a projection sentence. Returns (text, weekly_rec_id)."""
    if suggestion_service.latest_suggestion(conn, user_id) is None:
        suggestion_service.generate_suggestion(conn, user_id)
    weekly = suggestion_service.latest_suggestion(conn, user_id)
    parts = [REASONS[reason], "Here is what the rules can tell you.", weekly["text"]]
    four = context["projections"]["4_weeks"]
    if four["status"] == "ok":
        parts.append(projection.describe(four))
    return " ".join(parts), weekly["recommendation_id"]
 
 
def _save(conn, user_id, question, text, source, metric_ids, rule_ids) -> int:
    try:
        rec_id = conn.execute("INSERT INTO recommendations (user_id, content, source, question) VALUES (?,?,?,?)",
                              (user_id, text, source, question)).lastrowid
        for metric_id in metric_ids:
            conn.execute("INSERT OR IGNORE INTO recommendation_metrics (recommendation_id, metric_id) VALUES (?,?)",
                         (rec_id, metric_id))
        for rule_id in rule_ids:
            conn.execute("INSERT OR IGNORE INTO recommendation_rules (recommendation_id, rule_id) VALUES (?,?)",
                         (rec_id, rule_id))
        conn.commit()
        return rec_id
    except Exception:
        conn.rollback()
        raise
 
 
def ask(conn: sqlite3.Connection, user_id: int, question, consent_llm: bool, client=None,
        today: date | None = None) -> dict:
    """Raises ValueError (bad question) or LookupError (unknown user). Never raises because the AI failed."""
    question = llm_context.clean_question(question)
    if conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone() is None:
        raise LookupError("User not found")
    as_of = _as_of(conn, user_id, today)
    results = metrics_service.compute_all(conn, user_id, as_of, store=False)
    context = llm_context.build_context(conn, user_id, as_of, results)
 
    reason, reply = None, None
    if not consent_llm:
        reason = "no_consent"
    elif client is None:
        reason = "no_key"
    else:
        system, user_message = llm_context.build_prompt(context, question)
        try:
            reply = client.complete(system, user_message)
        except LLMUnavailable:
            reason = "unavailable"
        else:
            if llm_guard.check_reply(reply, context):
                reason = "guard"
 
    four = context["projections"]["4_weeks"]
    if reason is None:  # the AI answered and passed the checks
        cited = llm_guard.cited_ids(reply)
        text, source = llm_guard.finish_reply(reply), "llm"
        metric_ids = list(metrics_service.store_results(conn, user_id, results, as_of).values())
        rule_ids = [suggestion_service._ensure_rule(conn, "R" + e[1:])[0] for e in cited]
    else:
        text, weekly_id = _fallback_text(conn, user_id, context, reason)
        text, source, cited = f"{text}\n\n{suggestion_service.DISCLAIMER}", "rules", []
        metric_ids = [r[0] for r in conn.execute(
            "SELECT metric_id FROM recommendation_metrics WHERE recommendation_id = ?", (weekly_id,))]
        rule_ids = [r[0] for r in conn.execute(
            "SELECT rule_id FROM recommendation_rules WHERE recommendation_id = ?", (weekly_id,))]
 goienndkk
    rec_id = _save(conn, user_id, question, text, source, metric_ids, rule_ids)
    based_on = [suggestions.display_for(r["metric_type"], r["value"]) for r in conn.execute(
        "SELECT m.metric_type, m.value FROM recommendation_metrics rm JOIN metrics m ON m.metric_id = rm.metric_id "
        "WHERE rm.recommendation_id = ? ORDER BY m.metric_id", (rec_id,))]
    evidence = [item for item in context["evidence"] if item["id"] in cited]
    return {"recommendation_id": rec_id, "answer": text, "generated_by": source, "fallback_reason": reason,
            "fallback_message": REASONS.get(reason), "estimate": four["status"] == "ok", "projection": four,
            "based_on": based_on, "evidence": evidence, "disclaimer": suggestion_service.DISCLAIMER}}}
