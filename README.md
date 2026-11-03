# LinkedIn Amplifier

LinkedIn Amplifier is an agent skill (compatible with Codex, Claude Code, Antigravity, and other `SKILL.md` harnesses) for finding people in your first-degree network who consistently start useful discussions in your field. It builds a watchlist by topic and suggests fresh posts where you have something specific to contribute.

The reusable instructions live in [SKILL.md](skills/linkedin-amplifier/SKILL.md). Point your agent at that file and ask it to use your signed-in Chromium session or your open LinkedIn tab.

> Use the LinkedIn Amplifier skill to find first-degree connections who start substantive discussions about AI coding agents and product design. Give me a watchlist and three recent posts where I could add something from my own experience.

The first pass can reuse an existing network scan and sample 15–20 connections. It compares recent original posts, counts distinct people who participate, and looks for follow-up questions, examples, and exchanges between peers. Author replies and follower counts provide separate context. Post suggestions include evidence links and a concrete comment angle for you to review and post.

The skill also supports visible connection counts and follow-up on comments you post. It preserves capped counts such as “500+,” marks incomplete threads, and reports profile-view trends separately from observable replies and impressions.

Browser runs use one tab, space content-loading actions at least 15 seconds apart, and checkpoint after at most 30 such actions. The skill stops if LinkedIn shows a rate limit, verification prompt, or restriction.

To continue a scan, ask the agent to resume from its saved checkpoint (`temp/<account>/checkpoint.json`). It verifies the signed-in account and skips profiles and posts it has already inspected, saving structured outputs (`connections.csv`, `watchlist.csv`, `posts.csv`, `opportunities.csv`, and `outcomes.csv`) in the gitignored `temp/<account>/` directory.

See the [changelog](CHANGELOG.md) for changes to the workflow.

## Start with your LinkedIn export

In LinkedIn, go to **Me → Settings & Privacy → Data Privacy → Download your data** (also labeled **Get a copy of your data**). Request the archive that includes connections, download it, and extract `Connections.csv`. LinkedIn includes email addresses according to each connection's export privacy settings. [LinkedIn export instructions](https://www.linkedin.com/help/recruiter/answer/a566336)

From the repository root, run:

```sh
python3 scripts/import_linkedin_export.py --account your-profile-slug "/path/to/Connections.csv"
```

Use the export owner's profile slug, the part after `/in/` in their profile URL. The importer reads the extracted English-header CSV, including its optional notes and UTF-8 BOM. It reports skipped rows with missing or invalid profile links and seeds `temp/<account>/connections.csv` without browser visits. Reimporting fills missing values and preserves existing nonblank data, including follower counts. Company, position, and connection date remain in the original export. Imported profiles are candidates for browser inspection.

## Inventory your full network

Start the first batch overnight if convenient. Keep the signed-in browser available and ask Codex to use the skill with this prompt:

> Inventory my entire first-degree LinkedIn network. Save each completed profile locally and stop at the browsing limit. Resume from the same checkpoint when I ask for the next batch.

Plan to resume in batches over several days or longer for a large network. Each run keeps the 30-action limit and 15-second spacing, even overnight. Stop when LinkedIn presents a warning or checkpoint. These limits manage browsing volume.

Python 3.8+ on macOS or Linux saves one CSV row per canonical profile URL in `temp/<account>/connections.csv`. The columns are name, LinkedIn permalink, email visible under Contact info, and follower count. Missing values stay blank. The directory is created on first save and Git ignores its contents.

```sh
python3 scripts/save_connections.py --account your-profile-slug < /path/to/observations.jsonl
```

Each input line is a JSON object with keys `name`, `linkedin_permalink`, `email`, and `followers`. Replaying observations produces the same rows. A new nonblank value updates the corresponding field and a blank observation preserves the last known value.
