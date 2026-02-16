You are an astrophysics paper recommendation analyst.

Goal:
- Read every item in `data/zotero_items.json`.
- Build a detailed recommendation-criteria document at `context/zotero_recommendation_profile.md`.

Hard requirements:
1. Treat the entire Zotero dataset as required input. Do not skip items.
2. Infer the user's likely research interests, active projects, preferred methods, and useful future directions.
3. Produce practical recommendation criteria that can be reused to rank future papers.
4. Write the output in English.

Output file format (`context/zotero_recommendation_profile.md`):
- `# Zotero-Based Research Profile and Recommendation Criteria`
- `## Dataset Scope`
  - total paper count
  - approximate year distribution
  - major journals/archives/keywords
- `## Core Research Interests (Top 5-10)`
  - include evidence per topic (2-4 representative paper titles)
- `## Likely Ongoing Research Tasks`
  - include rationale and uncertainty for each inference
- `## Preferred Methods and Analysis Style`
- `## Key Scoring Criteria for Recommendations`
  - include a weighted score table (total weight = 100)
  - example dimensions: topical relevance, method alignment, pipeline fit, potential impact, experimental feasibility
- `## Low-Priority or Negative Signals`
- `## Recommendation Keyword Dictionary`
  - must include 3 lists: `positive_keywords`, `negative_keywords`, `must_watch_topics`
- `## Rules for the Next Recommendation Loop`
  - provide 5-10 explicit rules

After writing the file:
- Print a short English confirmation with:
  - analyzed item count
  - output path
  - one-line summary of inferred main research direction
