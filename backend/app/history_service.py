"""History and compare (frames 05a and 05b).

timeline: every saved profile snapshot, newest first, with the weight and the change since the one before.
compare:  two check-in dates side by side: weight, adherence, sleep consistency and the suggestion.

This file only READS the database. It never saves anything. The numbers come from the same
functions in metrics.py that the rest of the app uses, so a comparison can never disagree with Home.
"""
import json
from datetime import date, timedelta

from app import metrics


def _week_start(day):
    """The Monday of the week this date is in (weeks run Monday to Sunday)."""
    return day - timedelta(days=day.weekday())


def _check_user(conn, user_id):
    """Raise LookupError if there is no such user."""
    if conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone() is None:
        raise LookupError("User not found")


def _parse_day(text, label):
    """'2026-10-12' becomes a date. Anything else raises ValueError with a message the screen can show."""
    try:
        return date.fromisoformat(text)
    except (TypeError, ValueError):
        raise ValueError(label + " must be a date like 2026-10-12")


# ---------------------------------------------------------------- timeline
def timeline(conn, user_id):
    """All of the user's profile snapshots, newest first.

    Returns {"entries": [{"snapshot_id", "date", "kind", "weight", "change"}, ...]}
    kind   = "Baseline" (made at onboarding, no check-in) or "Check-in"
    change = weight minus the weight in the snapshot before it (None for the oldest one)

    Example entry: {"snapshot_id": 6, "date": "2026-10-12", "kind": "Check-in", "weight": 72.3, "change": -0.4}
    """
    _check_user(conn, user_id)
    rows = conn.execute(
        """SELECT s.snapshot_id, s.weight, c.checkin_id,
                  COALESCE(c.checkin_date, date(s.created_at)) AS day
           FROM profile_snapshots s LEFT JOIN checkins c ON c.snapshot_id = s.snapshot_id
           WHERE s.user_id = ?
           ORDER BY day, s.snapshot_id""", (user_id,)).fetchall()

    entries = []
    previous_weight = None
    for row in rows:  # oldest first, so each row can look back at the one before it
        change = None
        if previous_weight is not None and row["weight"] is not None:
            change = round(row["weight"] - previous_weight, 2)
        entries.append({
            "snapshot_id": row["snapshot_id"],
            "date": row["day"],
            "kind": "Check-in" if row["checkin_id"] is not None else "Baseline",
            "weight": row["weight"],
            "change": change,
        })
        if row["weight"] is not None:
            previous_weight = row["weight"]

    entries.reverse()  # the screen wants newest first
    return {"entries": entries}


# ----------------------------------------------------------------- compare
def _adherence_weeks_until(conn, user_id, until):
    """Like the adherence loader in metrics_service, but only uses check-ins up to and including `until`.

    Returns [(planned, done), ...] one pair per week, oldest first.
    """
    rows = conn.execute(
        """SELECT c.checkin_id, c.checkin_date, s.training_schedule
           FROM checkins c JOIN profile_snapshots s ON s.snapshot_id = c.snapshot_id
           WHERE c.user_id = ? AND c.checkin_date <= ? ORDER BY c.checkin_date""",
        (user_id, until)).fetchall()

    planned = {}  # Monday of the week -> number of planned sessions
    done = {}     # Monday of the week -> set of days trained
    for row in rows:
        week = _week_start(date.fromisoformat(row["checkin_date"][:10]))
        try:
            days = json.loads(row["training_schedule"] or "{}").get("days", [])
        except ValueError:
            days = []
        planned[week] = len(set(days))
        done.setdefault(week, set())
        logs = conn.execute(
            "SELECT DISTINCT session_day FROM workout_logs WHERE checkin_id = ? AND session_day IS NOT NULL",
            (row["checkin_id"],)).fetchall()
        for log in logs:
            done[week].add(log["session_day"])

    return [(planned[week], len(done[week])) for week in sorted(planned)]


def _sleep_entries_until(conn, user_id, until):
    """Like the sleep loader in metrics_service, but only up to and including `until`."""
    rows = conn.execute(
        """SELECT sl.bed_time, sl.wake_time FROM sleep_logs sl JOIN checkins c ON c.checkin_id = sl.checkin_id
           WHERE c.user_id = ? AND c.checkin_date <= ? AND sl.bed_time IS NOT NULL AND sl.wake_time IS NOT NULL
           ORDER BY c.checkin_date""", (user_id, until)).fetchall()
    return [(row["bed_time"], row["wake_time"]) for row in rows]


def _suggestion_for_day(conn, user_id, day):
    """The weekly suggestion made on this check-in date, or None.

    The suggestion is found through its metrics: they were saved with the check-in date as `computed_at`.
    If the database has a `question` column (AI answers), those answers are skipped.
    """
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(recommendations)")]
    only_weekly = " AND r.question IS NULL" if "question" in columns else ""
    row = conn.execute(
        """SELECT r.content FROM recommendations r
           JOIN recommendation_metrics rm ON rm.recommendation_id = r.recommendation_id
           JOIN metrics m ON m.metric_id = rm.metric_id
           WHERE r.user_id = ? AND substr(m.computed_at, 1, 10) = ?""" + only_weekly + """
           ORDER BY r.recommendation_id DESC LIMIT 1""", (user_id, day)).fetchone()
    return row["content"] if row else None


def _snapshot_for_day(conn, user_id, day):
    """Everything the compare screen shows for one check-in date. Raises ValueError if there is no check-in."""
    checkin = conn.execute(
        """SELECT c.checkin_id, s.weight, s.training_schedule
           FROM checkins c JOIN profile_snapshots s ON s.snapshot_id = c.snapshot_id
           WHERE c.user_id = ? AND c.checkin_date = ?""", (user_id, day)).fetchone()
    if checkin is None:
        raise ValueError("There is no check-in on " + day)

    adherence = metrics.adherence_pct(_adherence_weeks_until(conn, user_id, day))
    sleep = metrics.sleep_consistency_min(_sleep_entries_until(conn, user_id, day))
    return {
        "date": day,
        "weight": checkin["weight"],
        "adherence_pct": adherence.value if adherence.ok else None,
        "sleep_consistency_min": sleep.value if sleep.ok else None,
        "suggestion": _suggestion_for_day(conn, user_id, day),
    }


def _difference(from_value, to_value, decimals):
    """to minus from, or None when either side is missing."""
    if from_value is None or to_value is None:
        return None
    return round(to_value - from_value, decimals)


def compare(conn, user_id, from_day, to_day):
    """Put two check-in dates side by side.

    from_day and to_day are 'YYYY-MM-DD' texts and must both be dates the user checked in on,
    with from_day earlier than to_day.

    Returns {"from": {...}, "to": {...}, "change": {"weight", "adherence_pct", "sleep_consistency_min"}}
    A value is None when there was not enough data at that date (the screen says "Not enough data yet").
    Raises LookupError (no user) or ValueError (bad or missing dates).
    """
    _check_user(conn, user_id)
    start = _parse_day(from_day, "from")
    end = _parse_day(to_day, "to")
    if start >= end:
        raise ValueError("Pick a From date that is earlier than the To date")

    first = _snapshot_for_day(conn, user_id, start.isoformat())
    second = _snapshot_for_day(conn, user_id, end.isoformat())
    return {
        "from": first,
        "to": second,
        "change": {
            "weight": _difference(first["weight"], second["weight"], 2),
            "adherence_pct": _difference(first["adherence_pct"], second["adherence_pct"], 1),
            "sleep_consistency_min": _difference(first["sleep_consistency_min"], second["sleep_consistency_min"], 1),
        },
    }

