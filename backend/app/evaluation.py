"""Evaluation script (tickets T-35, T-36): run every persona, print the results table, check the expected rules.
 
Run from backend/:
    python -m app.evaluation                 # rules only, always works
    python -m app.evaluation --csv out.csv   # also write the table for the report
    python -m app.evaluation --llm           # also ask the real AI the same question (needs ANTHROPIC_API_KEY)
 
What this shows: on made-up personas built to behave in known ways, the rule engine picks the rule we expect.
What it does NOT show: that the advice improves anyone's health. That needs real users.
"""
from __future__ import annotations
 
import argparse
import csv
import sys
 
from . import db, llm_client, personas
 
COLUMNS = ("persona", "week", "date", "rule", "adherence", "trend", "sleep_spread")
 
 
def evaluate(client=None) -> tuple[list[dict], list[str]]:
    """Run all personas in a fresh in-memory database. Returns (rows, failures).
 
    A failure is a persona whose rule is not the expected one: R1 at week 1 (too little data) and the
    persona's own rule at week 12.
    """
    rows, failures = [], []
    for name, spec in personas.PERSONAS.items():
        conn = db.connect(":memory:")
        try:
            db.init_db(conn)
            found = personas.run_persona(conn, name, client=client)
        finally:
            conn.close()
        rows += found
        by_week = {r["week"]: r["rule"] for r in found}
        if by_week[1] != "R1":
            failures.append(f"{name}: week 1 gave {by_week[1]}, expected R1")
        if by_week[12] != spec["expected"]:
            failures.append(f"{name}: week 12 gave {by_week[12]}, expected {spec['expected']}")
    return rows, failures
 
 
def format_table(rows: list[dict]) -> str:
    """Plain-text table, one line per persona and week."""
    def cell(value):
        return "-" if value is None else (f"{value:.2f}" if isinstance(value, float) else str(value))
    widths = [max(len(c), *(len(cell(r.get(c))) for r in rows)) for c in COLUMNS]
    lines = ["  ".join(c.ljust(w) for c, w in zip(COLUMNS, widths)).rstrip()]
    lines += ["  ".join(cell(r.get(c)).ljust(w) for c, w in zip(COLUMNS, widths)).rstrip() for r in rows]
    return "\n".join(lines)
 
 
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the AdaptFit persona evaluation.")
    parser.add_argument("--csv", help="write the table to this CSV file")
    parser.add_argument("--llm", action="store_true", help="also ask the real AI (needs ANTHROPIC_API_KEY)")
    args = parser.parse_args(argv)
 
    client = None
    if args.llm:
        client = llm_client.get_client()
        if client is None:
            print("--llm needs the ANTHROPIC_API_KEY environment variable. Running rules only.")
    rows, failures = evaluate(client)
    print(format_table(rows))
    if client is not None:
        print("\nAI answers to:", personas.QUESTION)
        for r in rows:
            print(f"- {r['persona']} week {r['week']} [{r['ai_source']}]: {r['ai_answer'].splitlines()[0]}")
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(COLUMNS) + ["suggestion"], extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nWrote {args.csv}")
    if failures:
        print("\nFAILED:\n" + "\n".join(failures))
        return 1
    print(f"\nAll {len(personas.PERSONAS)} personas behave as expected.")
    return 0
 
 
if __name__ == "__main__":
    sys.exit(main())
