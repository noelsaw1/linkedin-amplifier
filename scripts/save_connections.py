#!/usr/bin/env python3
"""Merge browser observations from JSON Lines into a local LinkedIn CSV."""

import argparse
import csv
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit

FIELDS = ("name", "linkedin_permalink", "email", "followers")
ROOT = Path(__file__).resolve().parents[1]


def normalize(record):
    row = {field: str(record.get(field) or "").strip() for field in FIELDS}
    url = urlsplit(row["linkedin_permalink"])
    match = re.fullmatch(r"/in/([a-zA-Z0-9%_-]+)/?", url.path)
    if url.scheme != "https" or url.netloc.lower() not in {
        "linkedin.com", "www.linkedin.com"
    } or match is None:
        raise ValueError("Expected an HTTPS LinkedIn /in/ profile permalink")
    row["linkedin_permalink"] = f"https://www.linkedin.com/in/{match[1].lower()}/"
    followers = record.get("followers")
    if followers is not None and followers != "":
        count = str(followers).strip()
        if not re.fullmatch(r"[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+", count):
            raise ValueError("Followers must be an exact nonnegative integer or blank")
        row["followers"] = str(int(count.replace(",", "")))
    for field in ("name", "email"):
        if row[field].startswith(("=", "+", "-", "@")):
            row[field] = "'" + row[field]
    return row


def merge(path, observations):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        rows = {}
        if path.exists():
            with path.open(encoding="utf-8", newline="") as source:
                for record in csv.DictReader(source):
                    row = normalize(record)
                    rows[row["linkedin_permalink"]] = row
        for row in observations:
            permalink = row["linkedin_permalink"]
            previous = rows.get(permalink, {})
            rows[permalink] = {
                field: row[field] or previous.get(field, "") for field in FIELDS
            }
        with tempfile.NamedTemporaryFile(
            dir=path.parent, mode="w", encoding="utf-8", newline="", delete=False
        ) as output:
            staging = Path(output.name)
            try:
                writer = csv.DictWriter(output, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows(rows[url] for url in sorted(rows))
                output.flush()
                os.fsync(output.fileno())
                staging.replace(path)
            finally:
                staging.unlink(missing_ok=True)
        return len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account", required=True, help="Signed-in profile slug")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", args.account):
        parser.error("Account must be a LinkedIn profile slug")
    path = ROOT / "temp" / args.account.lower() / "connections.csv"
    try:
        observations = [normalize(json.loads(line)) for line in sys.stdin if line.strip()]
        total = merge(path, observations)
    except (ValueError, TypeError, AttributeError, OSError) as error:
        parser.exit(1, f"Save failed: {error}\n")
    print(f"{total} unique connections saved to {path}")


if __name__ == "__main__":
    main()
