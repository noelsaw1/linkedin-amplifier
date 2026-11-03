#!/usr/bin/env python3
"""Seed the local connection inventory from an extracted LinkedIn Connections.csv."""

import argparse
import csv
from pathlib import Path
import re

from save_connections import ROOT, merge, normalize


def read_export(source):
    required = {"First Name", "Last Name", "URL"}
    records = csv.reader(source, strict=True)
    for fields in records:
        header = [field.strip() for field in fields]
        if required.issubset(header):
            break
    else:
        raise ValueError("Missing Connections.csv header (First Name, Last Name, URL)")

    rows = {}
    skipped = 0
    for fields in records:
        if not any(field.strip() for field in fields):
            continue
        if len(fields) != len(header):
            raise ValueError(f"Unexpected column count near line {records.line_num}")
        record = dict(zip(header, fields))
        try:
            row = normalize({
                "name": " ".join(record[key].strip() for key in ("First Name", "Last Name")).strip(),
                "linkedin_permalink": record["URL"],
                "email": record.get("Email Address"),
            })
        except ValueError:
            skipped += 1
            continue
        url = row["linkedin_permalink"]
        previous = rows.get(url, {})
        rows[url] = {key: value or previous.get(key, "") for key, value in row.items()}
    return list(rows.values()), skipped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account", required=True, help="LinkedIn profile slug of export owner")
    parser.add_argument("csv_file", type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", args.account):
        parser.error("Account must be a LinkedIn profile slug")

    path = ROOT / "temp" / args.account.lower() / "connections.csv"
    try:
        with args.csv_file.open(encoding="utf-8-sig", newline="") as source:
            rows, skipped = read_export(source)
        if not rows:
            raise ValueError(f"No usable profile URLs ({skipped} skipped)")
        total = merge(path, rows, fill_missing=True)
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"Import failed: {error}\n")
    print(f"Read {len(rows)} unique export profiles, skipped {skipped} rows without usable URLs.")
    print(f"{total} unique connections in {path}")


if __name__ == "__main__":
    main()
