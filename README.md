# LinkedIn Amplifier

LinkedIn Amplifier is a Codex skill for finding people in your first-degree network who consistently start useful discussions in your field. It builds a watchlist by topic and suggests fresh posts where you have something specific to contribute.

The reusable instructions live in [SKILL.md](skills/linkedin-amplifier/SKILL.md). Point Codex at that file and ask it to use your signed-in Chromium session or your open LinkedIn tab.

> Use the LinkedIn Amplifier skill to find first-degree connections who start substantive discussions about AI coding agents and product design. Give me a watchlist and three recent posts where I could add something from my own experience.

The first pass can reuse an existing network scan and sample 15–20 connections. It compares recent original posts, counts distinct people who participate, and looks for follow-up questions, examples, and exchanges between peers. Author replies and follower counts provide separate context. Post suggestions include evidence links and a concrete comment angle for you to review and post.

The skill also supports visible connection counts and follow-up on comments you post. It preserves capped counts such as “500+,” marks incomplete threads, and reports profile-view trends separately from observable replies and impressions.

Browser runs use one tab, space content-loading actions at least 15 seconds apart, and checkpoint after at most 30 such actions. The skill stops if LinkedIn shows a rate limit, verification prompt, or restriction.

To continue a scan, ask Codex to resume from its saved checkpoint. It verifies the signed-in account and skips profiles and posts it has already inspected. Keep scan results and checkpoints outside this repository because they contain data from your network.

See the [changelog](CHANGELOG.md) for changes to the workflow.
