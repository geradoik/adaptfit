#!/usr/bin/env python3
"""Create GitHub milestones, labels and issues from docs/tickets.csv using the GitHub CLI (gh).

Usage (from the repo root, after `gh auth login` and pushing the repo):
    python scripts/create_issues.py            # dry run: prints what would be created
    python scripts/create_issues.py --run      # actually creates everything

Running --run twice creates duplicates, so only do it once.
"""
import argparse
import csv
import subprocess
import sys
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent.parent / "docs" / "tickets.csv"


def gh(args, dry_run):
    print("gh " + " ".join(f'"{a}"' if " " in a else a for a in args[:6]) + (" ..." if len(args) > 6 else ""))
    if dry_run:
        return
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if result.returncode != 0 and "already exists" not in result.stderr:
        sys.exit(f"gh failed: {result.stderr.strip()}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="create items (default is a dry run)")
    dry_run = not parser.parse_args().run

    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    milestones = sorted({r["milestone"] for r in rows})
    labels = sorted({label for r in rows for label in r["labels"].split(",") if label})

    for m in milestones:
        gh(["api", "repos/{owner}/{repo}/milestones", "-f", f"title={m}"], dry_run)
    for label in labels:
        gh(["label", "create", label, "--force"], dry_run)
    for r in rows:
        gh(["issue", "create", "--title", r["title"], "--body", r["body"],
            "--label", r["labels"], "--milestone", r["milestone"]], dry_run)

    print(f"\n{len(rows)} issues, {len(milestones)} milestones, {len(labels)} labels"
          + (" (dry run, nothing created; add --run to create)" if dry_run else " created"))


if __name__ == "__main__":
    main()
