# Project: Swiggy Voice-of-Customer Analyzer

## About the owner
The owner uses macOS (zsh terminal) and is new to coding. Always give
Mac commands: python3, `python3 -m pip`, `source .venv/bin/activate`. Explain plans and code in simple language,
avoid jargon or define it, and keep code simple and well commented.
Always show a plan before writing code and wait for approval.
Only work on the step the owner asks for. After finishing, summarise what
changed and tell the owner exactly which command to run to test it.

## Purpose
Portfolio project for PM, Business Analyst, Data Analyst, FDE, and GenAI roles.
Scrape Swiggy Play Store reviews, store them in SQLite, classify them with an LLM
into product themes, measure accuracy against manual labels, analyse trends with
SQL, and present insights in a Streamlit dashboard.

## Tech stack
- Python 3.10+, pandas
- google-play-scraper for data collection
- SQLite (built into Python via sqlite3); analysis done in SQL where possible
- Anthropic Python SDK for classification (structured JSON output)
- Streamlit + Plotly for the dashboard
- python-dotenv for loading the API key

## Rules
- Never hardcode API keys. Load from .env. Never commit .env.
- Never ask the owner to paste the API key into chat.
- Do not store usernames or profile images from reviews.
- Every script runs from the project root: `python3 src/<script>.py`
- Use file paths relative to the project root.
- Prefer SQL for aggregation; use pandas only where SQL is awkward.
- LLM calls must be resumable (skip already-classified reviews), support a
  --limit argument for small test runs, and print estimated cost.
- The deployed dashboard reads only CSV files in data/outputs/ and never calls the LLM.

## Current status
- [x] Step 0: Setup
- [x] Step 1: Scrape
- [x] Step 2: SQLite
- [x] Step 3: Clean
- [x] Step 4: Taxonomy + manual labels
- [x] Step 5: LLM classification
- [x] Step 6: Evaluation
- [x] Step 7: SQL analysis + impact score
- [x] Step 8: Dashboard + deploy
- [ ] Step 9: Insights memo
- [ ] Step 10: README + packaging