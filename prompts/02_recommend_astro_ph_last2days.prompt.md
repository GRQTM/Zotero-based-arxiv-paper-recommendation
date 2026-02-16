You are selecting astro-ph papers for the user.

Goal:
- Read `context/zotero_recommendation_profile.md`.
- Read all entries from `data/arxiv_astro_ph_last2days.json`.
- Recommend exactly 5 papers that best match the user's inferred research profile.

Hard requirements:
1. Process every paper entry in `data/arxiv_astro_ph_last2days.json` before ranking.
2. Use the scoring criteria and keyword rules from `context/zotero_recommendation_profile.md`.
3. Include all astro-ph subsections already present in the dataset (do not narrow the scope).
4. Write the response in English.

Selection constraints:
- Pick 5 papers only.
- Avoid near-duplicates in topic.
- Prefer papers that are both relevant and actionable for the user's ongoing work.

For each selected paper, include:
- Title
- Authors
- arXiv ID / Link
- 3-5 sentence summary
- Recommendation reason (connection to the user's research profile)
- Fit score (0-100)

Also include:
- `Total papers scanned`
- `Average fit score of the final top 5`
- `3 near-miss candidates` (one-line exclusion reason each)

Output:
- Write the full result directly to stdout (terminal output) in English.
- Do not write or modify any files.
- Use this exact final section title:
  - `## Shareable Recommendation Message`

Message format for the final section:
- short greeting
- top 5 list (for each paper, include all fields below in English):
  - Title
  - Authors (show up to 3 names, then use "et al." for remaining)
  - Link
  - Summary (2-3 sentences)
  - Why recommended (1-2 sentences)
- closing line with next scan suggestion

After finishing:
- Print a short English completion summary.
