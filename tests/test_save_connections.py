import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import save_connections  # noqa: E402


class SaveConnectionsTests(unittest.TestCase):
    def test_normalize_canonicalizes_urls_and_followers(self):
        row = save_connections.normalize(
            {
                "name": "  Ada Lovelace ",
                "linkedin_permalink": "https://uk.linkedin.com/in/Ada-Lovelace_1815/?trk=contact",
                "email": " ada@example.com ",
                "followers": "1,234",
            }
        )
        self.assertEqual(
            row,
            {
                "name": "Ada Lovelace",
                "linkedin_permalink": "https://www.linkedin.com/in/ada-lovelace_1815/",
                "email": "ada@example.com",
                "followers": "1234",
            },
        )

    def test_normalize_unifies_percent_encoded_and_unicode_slugs(self):
        upper_hex = save_connections.normalize(
            {"linkedin_permalink": "https://www.linkedin.com/in/Jos%C3%A9-Garc%C3%ADa"}
        )
        lower_hex = save_connections.normalize(
            {"linkedin_permalink": "https://linkedin.com/in/jos%c3%a9-garc%c3%ada/"}
        )
        raw_unicode = save_connections.normalize(
            {"linkedin_permalink": "https://www.linkedin.com/in/josé-garcía/"}
        )
        expected = "https://www.linkedin.com/in/jos%C3%A9-garc%C3%ADa/"
        self.assertEqual(upper_hex["linkedin_permalink"], expected)
        self.assertEqual(lower_hex["linkedin_permalink"], expected)
        self.assertEqual(raw_unicode["linkedin_permalink"], expected)

    def test_normalize_rejects_booleans_and_bad_urls_or_counts(self):
        bad_inputs = [
            "not-a-dict",
            {"linkedin_permalink": "https://www.linkedin.com/in/alice/", "followers": True},
            {"linkedin_permalink": "https://www.linkedin.com/in/alice/", "name": False},
            {"linkedin_permalink": "http://www.linkedin.com/in/alice/"},
            {"linkedin_permalink": "https://evil.example.com/in/alice/"},
            {"linkedin_permalink": "https://www.linkedin.com/company/acme/"},
            {"linkedin_permalink": "https://www.linkedin.com/in/alice%2Fbob/"},
            {"linkedin_permalink": "https://www.linkedin.com/in/alice/", "followers": "500+"},
            {"linkedin_permalink": "https://www.linkedin.com/in/alice/", "followers": "1.2K"},
            {"linkedin_permalink": "https://www.linkedin.com/in/alice/", "followers": "-5"},
        ]
        for payload in bad_inputs:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    save_connections.normalize(payload)

    def test_formula_escaping_and_merge_idempotency(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "account" / "connections.csv"
            first_batch = [
                save_connections.normalize(
                    {
                        "name": "=SUM(1,2)",
                        "linkedin_permalink": "https://www.linkedin.com/in/alice/",
                        "email": "+alice@example.com",
                        "followers": "0",
                    }
                ),
                save_connections.normalize(
                    {
                        "name": "Bob",
                        "linkedin_permalink": "https://www.linkedin.com/in/bob/",
                        "email": "bob@example.com",
                        "followers": "42",
                    }
                ),
            ]
            self.assertEqual(save_connections.merge(csv_path, first_batch), 2)

            second_batch = [
                save_connections.normalize(
                    {
                        "name": "",
                        "linkedin_permalink": "https://linkedin.com/in/ALICE",
                        "email": "",
                        "followers": "105",
                    }
                )
            ]
            self.assertEqual(save_connections.merge(csv_path, second_batch), 2)

            with csv_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(
                rows,
                [
                    {
                        "name": "'=SUM(1,2)",
                        "linkedin_permalink": "https://www.linkedin.com/in/alice/",
                        "email": "'+alice@example.com",
                        "followers": "105",
                    },
                    {
                        "name": "Bob",
                        "linkedin_permalink": "https://www.linkedin.com/in/bob/",
                        "email": "bob@example.com",
                        "followers": "42",
                    },
                ],
            )

    def test_cli_rejects_invalid_account_slug(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "save_connections.py"
        result = subprocess.run(
            [sys.executable, str(script), "--account", "../bad"],
            input=json.dumps({"linkedin_permalink": "https://www.linkedin.com/in/alice/"}) + "\n",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Account must be a LinkedIn profile slug", result.stderr)


if __name__ == "__main__":
    unittest.main()
