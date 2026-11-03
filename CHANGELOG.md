# Changelog

## Unreleased

- Added a Codex skill that finds first-degree LinkedIn connections who consistently draw substantive discussion and recommends up to three recent posts to comment on.
- Added an optional workflow for tracking replies, visible comment impressions, and profile-view trends.
- Preserved exact, capped, and unavailable connection counts as separate categories.
- Added single-tab browsing, a minimum of 15 seconds between content loads, a 30-action budget per run, and checkpoints for resuming. The skill stops on rate limits, verification prompts, and account restrictions.
- Added a resumable full-network inventory and a Python CSV writer that deduplicates by profile permalink and saves privately under `temp/`.
- Hardened `scripts/save_connections.py` to normalize percent-encoded/Unicode and regional LinkedIn `/in/` slugs, reject boolean values and encoded path separators, and added a standard-library `unittest` suite in `tests/test_save_connections.py`.
- Standardized deterministic schemas under `temp/<account>/` (`checkpoint.json`, `watchlist.csv`, `posts.csv`, `opportunities.csv`, `outcomes.csv`) and clarified per-run 30-action budget allocation in `SKILL.md`.
