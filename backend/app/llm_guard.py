from __future__ import annotations
 
import re
 
from .suggestion_service import DISCLAIMER
 
REPLY_MAX = 1500
KCAL_FLOOR = 1200   # design choice: a common minimum for unsupervised adults. Any lower daily figure is blocked.
BANNED_WORDS = ("starve", "starvation", "laxative", "purge", "diet pill", "steroid", "fast for 24", "water fast")
 
_CITATION = re.compile(r"\[E(\d+)\]")
_EXERCISE = re.compile(r"\[\[(.+?)\]\]")
_KCAL = re.compile(r"(\d[\d,]*)\s*(?:kcal|calories|cals?)\b", re.IGNORECASE)
 
 
def check_reply(reply, context: dict) -> list[str]:
    """Problems found in `reply`, or [].
 
    Example: check_reply("Do [[Burpees]] [E9]", ctx) -> ["Unknown exercise: Burpees", "Unknown citation: [E9]"]
    """
    if not isinstance(reply, str) or not reply.strip():
        return ["Empty reply"]
    problems = []
    if len(reply) > REPLY_MAX:
        problems.append(f"Reply longer than {REPLY_MAX} characters")
 
    known_evidence = {item["id"] for item in context["evidence"]}
    for number in sorted(set(_CITATION.findall(reply))):
        if f"E{number}" not in known_evidence:
            problems.append(f"Unknown citation: [E{number}]")
 
    allowed = {name.lower() for names in context["allowed_exercises"].values() for name in names}
    for name in dict.fromkeys(m.strip() for m in _EXERCISE.findall(reply)):
        if name.lower() not in allowed:
            problems.append(f"Unknown exercise: {name}")
 
    for amount in _KCAL.findall(reply):
        if int(amount.replace(",", "")) < KCAL_FLOOR:
            problems.append(f"Calorie figure below {KCAL_FLOOR}: {amount}")
 
    lowered = reply.lower()
    for word in BANNED_WORDS:
        if word in lowered:
            problems.append(f"Unsafe wording: {word}")
    return problems
 
 
def cited_ids(reply: str) -> list[str]:
    """Evidence ids used in the reply, in order, without repeats. 'Try [E3] and [E3] [E2]' -> ['E3', 'E2']."""
    return list(dict.fromkeys("E" + n for n in _CITATION.findall(reply)))
 
 
def finish_reply(reply: str) -> str:
    """Prepare a checked reply for display: drop the [[ ]] exercise markers and add the not-medical-advice line."""
    shown = _EXERCISE.sub(lambda m: m.group(1).strip(), reply.strip())
    return f"{shown}\n\n{DISCLAIMER}"

