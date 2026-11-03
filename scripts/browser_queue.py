#!/usr/bin/env python3
"""Report local inventory coverage or plan the next browser batch."""

import argparse
import csv
import json
import re

from save_connections import ROOT, normalize

ACTION_CAP = 30


def permalink(value):
    return normalize({"linkedin_permalink": value})["linkedin_permalink"]


def read_state(directory, account):
    inventory = directory / "connections.csv"
    profiles = set()
    if inventory.exists():
        with inventory.open(encoding="utf-8", newline="") as source:
            profiles = {permalink(row["linkedin_permalink"]) for row in csv.DictReader(source)}
    checkpoint = directory / "checkpoint.json"
    state = json.loads(checkpoint.read_text(encoding="utf-8")) if checkpoint.exists() else {}
    if not isinstance(state, dict) or state.get("account", account).lower() != account:
        raise ValueError("Checkpoint does not belong to the requested account")
    buckets = {}
    for name in ("inspected", "pending", "inaccessible"):
        values = state.get(f"{name}_urls", [])
        if not isinstance(values, list) or not all(isinstance(url, str) for url in values):
            raise ValueError(f"Expected a list of profile URLs for {name}_urls")
        buckets[name] = {permalink(url) for url in values}
    return profiles, state, buckets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    status = commands.add_parser("status")
    batch = commands.add_parser("next-batch")
    for command in (status, batch):
        command.add_argument("--account", required=True)
    batch.add_argument("--priority-url", action="append", default=[],
                       help="Verified topic match in preference order. Repeat as needed.")
    batch.add_argument("--budget", type=int, default=ACTION_CAP)
    batch.add_argument("--actions-used", type=int, default=0,
                       help="Actions already spent in the current browser run")
    batch.add_argument("--actions-per-profile", type=int, default=4)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", args.account):
        parser.error("Account must be a LinkedIn profile slug")
    account = args.account.lower()
    try:
        profiles, state, buckets = read_state(ROOT / "temp" / account, account)
        inaccessible = buckets["inaccessible"]
        inspected = buckets["inspected"] - inaccessible
        queued = (profiles | buckets["pending"]) - inspected - inaccessible
        result = {
            "account": account,
            "inventory_profiles": len(profiles),
            "inventory_uninspected": len(profiles & queued),
            "inspected": len(inspected),
            "inaccessible": len(inaccessible),
            "pending": len(queued),
            "blocker": state.get("blocker"),
        }
        if args.command == "next-batch":
            if not 1 <= args.budget <= ACTION_CAP or not 0 <= args.actions_used <= args.budget:
                parser.error("Require 1 <= budget <= 30 and 0 <= actions-used <= budget")
            if not 1 <= args.actions_per_profile <= ACTION_CAP:
                parser.error("Actions per profile must be between 1 and 30")
            priority = dict.fromkeys(permalink(url) for url in args.priority_url)
            remaining = args.budget - args.actions_used
            ordered = [url for url in priority if url in queued]
            ordered.extend(sorted(queued - priority.keys()))
            selected = [] if result["blocker"] else ordered[:remaining // args.actions_per_profile]
            result.update(
                remaining_actions=remaining,
                estimated_actions=len(selected) * args.actions_per_profile,
                profiles=selected,
            )
    except (OSError, ValueError, TypeError, AttributeError, KeyError, csv.Error) as error:
        parser.exit(1, f"Queue failed: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
