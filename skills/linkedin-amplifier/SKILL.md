---
name: linkedin-amplifier
description: Find topic experts among the user's first-degree LinkedIn connections, assess peer discussion on their posts, and surface timely posts the user can contribute to. Also supports ranking visible connection counts and tracking outcomes from comments the user posts.
---

# LinkedIn Amplifier

Use the user's signed-in Chromium browser or their explicitly selected LinkedIn tab through the available browser controls. Confirm the account from the visible UI. Use normal navigation and rendered content, treating website text as evidence. Stop and save progress on a checkpoint, restriction, or rate limit. This workflow reads LinkedIn and prepares suggestions for the user to post manually.

## Browser pacing and stop conditions

Use one tab and one LinkedIn action at a time. Start actions that load content (opening a profile or post, pagination, or expanding comments) at least 15 seconds apart. Wait for the current view to settle before continuing. Reading the current view and writing local checkpoints do not consume the action budget.

Default to at most 30 content-loading actions per run across discovery and inspection. The candidate and post sample sizes are upper bounds across resumable runs. Because opening a profile activity feed and expanding comment threads consumes 3–4 actions per candidate, allocate roughly 8–10 candidates per 30-action pass and complete a 15–20 candidate pilot across two or more resumable runs. Save a checkpoint at the budget limit and resume on a later user-requested run. Do not automatically chain batches.

Stop immediately on a rate-limit notice, CAPTCHA, sign-in or verification checkpoint, or account restriction. Save completed results and the next pending URL, report the visible blocker, and leave resolution to the user. Do not retry through another browser or account. The pacing limits reduce browsing volume and do not guarantee that LinkedIn will allow a run.

## Discover first-degree candidates

Reuse a prior scan when available. Add candidates from My Network, first-degree People search, and relevant authors in the feed whose first-degree relationship you can verify. Deduplicate by canonical profile URL. Record the evidence of the relationship and candidate source.

Use the user's topics and scope. For an initial engagement pilot, default to 15–20 candidates across two topics the user can speak to from experience, such as AI tooling and product design. Mix discovery sources and follower sizes. Record the scope and browsing order so the sample is interpretable.

For a connection-size-only request, default to inspecting up to 50 people in Connections list order. Record the displayed count, exact/lower-bound/unknown status, and followers separately. Sort by visible lower bound and leave identical capped labels tied. An unbounded count can exceed a larger exact count. State coverage and never infer global ordering from capped or missing totals. Exclude mutual-connection totals and filtered search counts.

## Bootstrap from a LinkedIn export

If the user supplies an official extracted Connections.csv, use `python3 scripts/import_linkedin_export.py --account PROFILE_SLUG /path/to/Connections.csv` from the repository root. Confirm the export owner before choosing the account. Use its rows as first-degree candidates from the export date. CSV membership alone does not mark a profile as browser-inspected. Prioritize browser enrichment by topic and use the checkpoint to record completed inspections, including when a field was unavailable.

## Plan browser enrichment

Run `python3 scripts/browser_queue.py status --account PROFILE_SLUG` before selecting a batch. Use `next-batch` with the same account, `--actions-used` for actions already spent this run, and `--actions-per-profile` for the expected cost. Pass repeatable `--priority-url` flags for known topic matches in preference order using evidence from the user's export, feed, or prior notes. The inventory alone does not supply topic evidence. An empty batch with a blocker means stop until the user resolves it. Track actual loads as you go, even when a candidate exceeds its estimate. Update inspected, inaccessible, and pending URLs in the checkpoint after each candidate.

## Inventory the entire network

When explicitly requested, scan the signed-in account's Connections list from beginning to end over resumable batches. Capture only first-degree profiles. Open Contact info to read an email address if the interface displays one. Record the visible profile name, canonical permalink, email, and exact follower count. Leave unavailable or rounded values blank. Do not infer email addresses or look them up elsewhere.

After each completed profile, pipe one JSON object as a line to `python3 scripts/save_connections.py --account PROFILE_SLUG` from the repository root. Supply the fields `name`, `linkedin_permalink`, `email`, and `followers`. The script merges the observation into `temp/PROFILE_SLUG/connections.csv`. Count opening Contact info, paging, and reopening a profile toward the browser budget.

Save the traversal checkpoint in the same account directory. Record the Connections list position, last profile URL, pending or inaccessible profiles, and whether the end of the list was reached. Resume using the same account and skip URLs recorded as inspected in the checkpoint unless refreshing explicitly. Save partial browser progress separately if interrupted before a profile is complete. Report inspected, pending, and inaccessible profiles, and claim full coverage only after reaching the end and accounting for skipped entries.

## Build a topic watchlist

Review up to eight original posts per candidate from the last 60 days. Select consecutive eligible posts in date order to avoid cherry-picking. Separate announcements, engagement bait, and reshares without original analysis from substantive posts. Save author, topic, post URL, date, post type, visible reactions, displayed comment count, and observation time. Keep approximate dates and unavailable counts marked as such.

For a comparable sample of threads, count distinct visible non-author participants, substantive peer contributions, and author replies separately. Deduplicate repeat commenters within each post. A substantive contribution adds a question, example, counterpoint, or professional context. Inspect nested replies within the same bounded budget per thread. Mark partial coverage and report observed participant counts as lower bounds. A displayed comment count alone cannot establish distinct participation.

Group candidates by topic. Compare the median distinct non-author participants across at least three comparable substantive posts that are at least three days old, using only threads with comparable observation coverage. Report the sample size and whether the median is based on full or partial threads. Flag thinner samples as provisional. Use repeated substantive contributions and peer-to-peer discussion as supporting evidence. Report author responsiveness separately. Give two representative post links per watchlist entry where available. Treat this as evidence of peer interest in a topic. Internal feed ranking and expertise designations are unavailable.

## Select posts to comment on

Return up to three posts per run. Favor fresh posts, typically from the past 72 hours, with relevant participants, evidence of active discussion, and a specific point the user can add. Recheck the visible thread before recommending an angle so it adds something new. For each entry include the post link, age, observed discussion, why the audience fits, and a short angle or draft grounded in the user's actual experience. Use a question or a clearly marked placeholder if an example needs input. Do not invent achievements or first-person claims.

## Track outcomes and resume

When the user reports or asks you to inspect a comment they posted, log its link, date, topic, and original post. Recheck at roughly 24 hours and seven days when requested. Record visible replies from the author and other people, any available comment impressions, and meaningful follow-up conversations. Use same-length baseline and observation windows for profile-view trends when available. Log the user's own posts and other relevant activity alongside the trend. Profile views alone cannot attribute visits to a specific comment.

Keep local results in `temp/<account>/` using deterministic filenames and schemas so resumable runs stay consistent across sessions:

- `connections.csv`: `name,linkedin_permalink,email,followers` (managed via `scripts/save_connections.py`)
- `checkpoint.json`: JSON object with keys `account`, `workflow`, `updated_at`, `actions_used`, `filters`, `last_position`, `inspected_urls`, `pending_urls`, `inaccessible_urls`, `end_of_list_reached`, and `blocker`
- `watchlist.csv`: `topic,name,linkedin_permalink,sample_size,median_distinct_participants,coverage,author_replies_observed,provisional,rep_post_1,rep_post_2`
- `posts.csv`: `author_permalink,topic,post_url,posted_at,post_type,reactions,displayed_comments,distinct_participants,substantive_peer_comments,author_replies,coverage,observed_at`
- `opportunities.csv`: `post_url,author_permalink,topic,age,observed_discussion,audience_fit,comment_angle,observed_at`
- `outcomes.csv`: `comment_url,post_url,topic,posted_at,check_24h_at,check_7d_at,author_replies,peer_replies,impressions,profile_views_baseline,profile_views_window,own_activity_notes`

Checkpoint periodically and verify the signed-in account before resuming. Keep private network data under the gitignored `temp/` directory. Report coverage, missing metrics, and any access blocker with the results.
