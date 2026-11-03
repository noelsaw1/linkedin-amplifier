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
from urllib.parse import quote, unquote, urlsplit

FIELDS = ("name", "linkedin_permalink", "email", "followers")
ROOT = Path(__file__).resolve().parents[1]


def normalize(record):
    if not isinstance(record, dict):
        raise ValueError("Observation must be a JSON object")
    row = {}
    for field in FIELDS:
        raw = record.get(field)
        if isinstance(raw, bool):
            raise ValueError(f"Field '{field}' must not be a boolean")
        row[field] = str(raw if raw is not None else "").strip()

    url = urlsplit(row["linkedin_permalink"])
    host = (url.hostname or "").lower()
    match = re.fullmatch(r"/in/([^/?#]+)/?", url.path)
    if (
        url.scheme != "https"
        or url.port is not None
        or not (
            host in {"linkedin.com", "www.linkedin.com"}
            or re.fullmatch(r"[a-z]{2}\.linkedin\.com", host)
        )
        or match is None
    ):
        raise ValueError("Expected an HTTPS LinkedIn /in/ profile permalink")
    slug = unquote(match[1]).strip().lower()
    if not slug or not re.fullmatch(r"[\w-]+", slug):
        raise ValueError("Expected an HTTPS LinkedIn /in/ profile permalink")
    row["linkedin_permalink"] = f"https://www.linkedin.com/in/{quote(slug, safe='-_')}/"

    followers = record.get("followers")
    if followers is not None and str(followers).strip() != "":
        count = str(followers).strip()
        if not re.fullmatch(r"[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+", count):
            raise ValueError("Followers must be an exact nonnegative integer or blank")
        row["followers"] = str(int(count.replace(",", "")))
    else:
        row["followers"] = ""

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
