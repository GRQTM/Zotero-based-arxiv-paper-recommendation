# arxiv_ph_rcmd

## Quick Start (for Codex users)
1. Clone the repository and enter the folder
   - `cd /path/to/arxiv_ph_rcmd`
2. Run
   - `./start`

Default behavior:
- If `context/zotero_recommendation_profile.md` does not exist, it is auto-initialized from `templates/zotero_recommendation_profile.sample.md`.
- This means recommendations can run even without a Zotero API key.

## Run Commands
- `./start` (recommendation only, using existing/template profile)
- `./start -r` (refresh Zotero-based profile, then run recommendation)
- `npm start`
- or `bash ./start.sh`

## Workflow
1. `./start`:
   - Uses `context/zotero_recommendation_profile.md`
   - Auto-creates it from template if missing
   - Fetches arXiv astro-ph papers from the last 2 days (including subsections)
   - Prints top-5 recommendation message directly to terminal
2. `./start -r`:
   - Fetches Zotero library metadata/abstracts via Zotero API
   - Rebuilds research profile (recommendation criteria) via Codex prompt
   - Fetches arXiv astro-ph papers from the last 2 days (including subsections)
   - Prints top-5 recommendation message directly to terminal

## Key Files
- `scripts/fetch_zotero_library.py`
- `scripts/fetch_arxiv_astro_ph.py`
- `prompts/01_build_zotero_profile.prompt.md`
- `prompts/02_recommend_astro_ph_last2days.prompt.md`
- `templates/zotero_recommendation_profile.sample.md`
- `context/zotero_recommendation_profile.md`
- `data/arxiv_astro_ph_last2days_summary.md`
- The shareable message is printed directly in terminal output.

## Codex Binary Path
- Default:
  - `/Applications/Codex.app/Contents/Resources/codex`
- If not found, the script auto-detects `codex` from system PATH.
- Manual override:
  - `CODEX_BIN=/custom/path/to/codex ./start`

## API Keys
- Zotero API key is required only for `./start -r`.
- By default, the script reads `.zotero_api_key`.
- Or set `ZOTERO_API_KEY` as an environment variable.
- `start.sh` auto-applies `600` permission to `.zotero_api_key`.
- For safety, keys are passed via environment variable only (not CLI arguments).
- Optional: set `.zotero_user_id` or `ZOTERO_USER_ID` to skip key lookup API call.
