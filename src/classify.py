"""
Step 5: Ask Claude to classify reviews into the themes in docs/taxonomy.md.

Run it from the project root:
    python3 src/classify.py --limit 40      # small test run first
    python3 src/classify.py                 # everything except the 200 labelled
    python3 src/classify.py --only-labeled  # only the 200, for Step 6

Reads:  usable reviews from data/swiggy_reviews.db
Writes: the classifications table in the same database
        logs/classify_failures.log when a batch cannot be classified

Safe to stop and restart. Reviews already classified are skipped, so you
never pay to classify the same review twice.
"""

import argparse
import json
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import pandas as pd
from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

DATABASE_PATH = Path("data/swiggy_reviews.db")
TAXONOMY_PATH = Path("docs/taxonomy.md")
REFERENCE_PATH = Path("data/labels/reference_labels.csv")
FAILURE_LOG_PATH = Path("logs/classify_failures.log")

MODEL = "claude-haiku-4-5-20251001"

BATCH_SIZE = 20        # reviews sent in one request
MAX_TOKENS = 8000      # room for 20 answers
MAX_ATTEMPTS = 2       # the first try, plus one retry
PAUSE_SECONDS = 0.5    # small gap between requests

# Haiku 4.5 prices, in US dollars per million tokens.
COST_PER_MILLION_INPUT = 1.00
COST_PER_MILLION_OUTPUT = 5.00
COST_PER_MILLION_CACHE_READ = 0.10   # cached input costs about a tenth
COST_PER_MILLION_CACHE_WRITE = 1.25  # writing to the cache costs a little extra

# The allowed answers for everything except themes, which come from the
# taxonomy file so they only ever live in one place.
SENTIMENTS = ["positive", "neutral", "negative"]
BUSINESS_LINES = ["Food", "Instamart", "Dineout", "General"]
SEVERITIES = [1, 2, 3]

TOOL_NAME = "record_classifications"


def read_taxonomy():
    """
    Read docs/taxonomy.md and pull out the theme names.

    The names come from the "### 1. Delivery timing" style headings, so
    editing the taxonomy file changes both the instructions we send and the
    list of answers we allow. Nothing is typed twice.
    """
    if not TAXONOMY_PATH.exists():
        print(f"No taxonomy found at {TAXONOMY_PATH}")
        sys.exit(1)

    text = TAXONOMY_PATH.read_text(encoding="utf-8")
    theme_names = re.findall(r"^### \d+\. (.+)$", text, re.MULTILINE)

    if not theme_names:
        print(f"Could not find any '### 1. Theme name' headings in {TAXONOMY_PATH}")
        sys.exit(1)

    return text, [name.strip() for name in theme_names]


def build_tool(theme_names):
    """
    Describe the exact shape of the answer we want back.

    This is "tool use": instead of asking for JSON in words and hoping, we
    hand Claude a form to fill in. "strict": True makes the API enforce it,
    so an invented theme name or sentiment simply cannot come back.
    """
    one_review = {
        "type": "object",
        "properties": {
            "review_id": {
                "type": "string",
                "description": "The exact review_id given in the message.",
            },
            "themes": {
                "type": "array",
                "items": {"type": "string", "enum": theme_names},
                "minItems": 1,
                "description": "One to three themes, most important first.",
            },
            "sentiment": {"type": "string", "enum": SENTIMENTS},
            "business_line": {"type": "string", "enum": BUSINESS_LINES},
            "severity": {"type": "integer", "enum": SEVERITIES},
            "summary": {
                "type": "string",
                "description": "One short line saying what the reviewer is talking about.",
            },
        },
        "required": [
            "review_id", "themes", "sentiment",
            "business_line", "severity", "summary",
        ],
        "additionalProperties": False,
    }

    return {
        "name": TOOL_NAME,
        "description": "Record the classification for every review in the message.",
        "input_schema": {
            "type": "object",
            "properties": {
                "classifications": {"type": "array", "items": one_review},
            },
            "required": ["classifications"],
            "additionalProperties": False,
        },
        "strict": True,
    }


def build_system_prompt(taxonomy_text):
    """
    The instruction sheet. It is the same on every request, so we mark it to
    be cached - repeat requests are then billed at about a tenth for this part.
    """
    instructions = (
        "You classify customer reviews of the Swiggy app using the taxonomy below.\n\n"
        "Rules:\n"
        "- Use ONLY the theme names exactly as written in the taxonomy.\n"
        "- Give one theme per review where possible, at most three, most important first.\n"
        "- Judge only what the text actually says. Do not guess an unstated cause.\n"
        "- Hindi, Hinglish, Bengali, Tamil and other languages are normal. Read them\n"
        "  as they are and do not translate them.\n"
        "- Use business_line 'General' unless the review clearly names one.\n"
        "- Severity is about harm to the customer, not how angry the writing sounds.\n"
        "- Return exactly one entry for every review_id you are given, and no others.\n\n"
        "===== TAXONOMY =====\n\n"
    )

    return [
        {
            "type": "text",
            "text": instructions + taxonomy_text,
            "cache_control": {"type": "ephemeral"},
        }
    ]


def build_user_message(batch):
    """Lay the batch out as a numbered list, each review tagged with its id."""
    parts = [f"Classify all {len(batch)} reviews below.\n"]
    for number, (review_id, content) in enumerate(batch, start=1):
        text = " ".join(str(content).split())
        parts.append(f"[{number}] review_id: {review_id}\n{text}\n")
    return "\n".join(parts)


def find_tool_result(response):
    """Pull the filled-in form out of the reply, or return None."""
    for block in response.content:
        if block.type == "tool_use" and block.name == TOOL_NAME:
            return block.input
    return None


def keep_good_records(answer, wanted_ids, theme_names):
    """
    Pick out the entries that are complete and sensible.

    Claude sometimes returns 19 answers for 20 reviews - it quietly skips one.
    Rather than throw away nineteen good answers and pay to ask again, we keep
    what is usable and let the caller re-ask for only the ones that are missing.
    """
    if not isinstance(answer, dict) or "classifications" not in answer:
        return []

    good = []
    seen = set()

    for record in answer["classifications"]:
        review_id = record.get("review_id")

        # Not one we asked for, or a duplicate of one we already have.
        if review_id not in wanted_ids or review_id in seen:
            continue

        themes = record.get("themes") or []
        if not themes or any(theme not in theme_names for theme in themes):
            continue
        if record.get("sentiment") not in SENTIMENTS:
            continue
        if record.get("business_line") not in BUSINESS_LINES:
            continue
        if record.get("severity") not in SEVERITIES:
            continue
        if not str(record.get("summary", "")).strip():
            continue

        seen.add(review_id)
        good.append(record)

    return good


def log_failure(batch_ids, reason):
    """Write a failed batch to the log file so nothing disappears silently."""
    FAILURE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    when = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with FAILURE_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{when}  {reason}\n")
        for review_id in batch_ids:
            log_file.write(f"    {review_id}\n")


def classify_batch(client, tool, system_prompt, batch, theme_names, totals):
    """
    Classify one batch and return the records we managed to get.

    Sends the batch, keeps whatever came back correctly, then asks again for
    only the reviews that were skipped. Anything still missing after the
    retry is written to the failure log.
    """
    still_needed = list(batch)
    collected = []
    last_problem = "unknown problem"

    for attempt in range(1, MAX_ATTEMPTS + 1):
        if not still_needed:
            break

        wanted_ids = {review_id for review_id, _ in still_needed}

        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system_prompt,
                tools=[tool],
                tool_choice={"type": "tool", "name": TOOL_NAME},
                messages=[{"role": "user",
                           "content": build_user_message(still_needed)}],
            )
        except anthropic.AuthenticationError:
            print("\nYour API key was rejected. Check ANTHROPIC_API_KEY in .env")
            sys.exit(1)
        except anthropic.RateLimitError:
            last_problem = "rate limited"
            print("  rate limited, waiting 20 seconds")
            time.sleep(20)
            continue
        except anthropic.APIStatusError as error:
            last_problem = f"API error {error.status_code}"
            print(f"  {last_problem}")
            time.sleep(5)
            continue
        except anthropic.APIConnectionError:
            last_problem = "could not reach the API"
            print(f"  {last_problem}")
            time.sleep(5)
            continue

        # Count the tokens whatever the answer turns out to be - they are paid for.
        usage = response.usage
        totals["input"] += usage.input_tokens
        totals["output"] += usage.output_tokens
        totals["cache_read"] += getattr(usage, "cache_read_input_tokens", 0) or 0
        totals["cache_write"] += getattr(usage, "cache_creation_input_tokens", 0) or 0

        answer = find_tool_result(response)
        if answer is None:
            last_problem = "Claude did not fill in the form"
            continue

        good = keep_good_records(answer, wanted_ids, theme_names)
        collected.extend(good)

        done_ids = {record["review_id"] for record in good}
        still_needed = [pair for pair in still_needed if pair[0] not in done_ids]

        if still_needed:
            last_problem = f"{len(still_needed)} reviews skipped by the model"
            if attempt < MAX_ATTEMPTS:
                print(f"  {last_problem} - asking again for just those")

    if still_needed:
        log_failure([review_id for review_id, _ in still_needed], last_problem)

    return collected


def choose_reviews(connection, only_labeled, limit):
    """Work out which reviews still need classifying."""
    usable = pd.read_sql_query(
        "SELECT review_id, content FROM reviews WHERE is_usable = 1 ORDER BY review_id",
        connection,
    )

    already_done = {
        row[0] for row in connection.execute("SELECT review_id FROM classifications")
    }

    if not REFERENCE_PATH.exists():
        print(f"No labelled file found at {REFERENCE_PATH}")
        print("Run this first:  python3 src/sample_for_labeling.py")
        sys.exit(1)

    labelled_ids = set(
        pd.read_csv(REFERENCE_PATH, encoding="utf-8-sig")["review_id"]
    )

    if only_labeled:
        wanted = usable[usable["review_id"].isin(labelled_ids)]
    else:
        wanted = usable[~usable["review_id"].isin(labelled_ids)]

    todo = wanted[~wanted["review_id"].isin(already_done)]

    print(f"Usable reviews          {len(usable):>6,}")
    print(f"Held back for Step 6    {len(labelled_ids):>6,}")
    print(f"Already classified      {len(already_done):>6,}")
    print(f"To classify now         {len(todo):>6,}"
          + ("  (labelled set only)" if only_labeled else ""))

    if limit:
        todo = todo.head(limit)
        print(f"Limited to             {len(todo):>6,}")

    return list(todo.itertuples(index=False, name=None))


def save_records(connection, records):
    """Write one batch of answers into the classifications table."""
    when = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = [
        (
            r["review_id"],
            json.dumps(r["themes"]),        # SQLite has no list type, so store JSON text
            r["sentiment"],
            r["business_line"],
            r["severity"],
            r["summary"].strip(),
            MODEL,
            when,
        )
        for r in records
    ]
    connection.executemany(
        """
        INSERT OR IGNORE INTO classifications
            (review_id, themes, sentiment, business_line,
             severity, summary, model, classified_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    connection.commit()


def report_cost(totals, classified_count):
    """Print what was used and what it works out to per 1,000 reviews."""
    cost = (
        totals["input"] / 1_000_000 * COST_PER_MILLION_INPUT
        + totals["output"] / 1_000_000 * COST_PER_MILLION_OUTPUT
        + totals["cache_read"] / 1_000_000 * COST_PER_MILLION_CACHE_READ
        + totals["cache_write"] / 1_000_000 * COST_PER_MILLION_CACHE_WRITE
    )

    print("\nTokens used")
    print(f"    input          {totals['input']:>9,}")
    print(f"    output         {totals['output']:>9,}")
    print(f"    read from cache{totals['cache_read']:>9,}")
    print(f"    written to cache{totals['cache_write']:>8,}")

    if totals["cache_read"] == 0 and totals["cache_write"] > 0:
        print("    (nothing was read from the cache - the taxonomy may be")
        print("     too short to cache, which is fine, just slightly dearer)")

    print(f"\nCost this run              ${cost:.4f}")
    if classified_count:
        per_thousand = cost / classified_count * 1000
        print(f"Estimated per 1,000 reviews ${per_thousand:.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="Classify Swiggy reviews with Claude."
    )
    parser.add_argument(
        "--only-labeled",
        action="store_true",
        help="Classify ONLY the 200 hand-labelled reviews (needed for Step 6).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Stop after this many reviews. Useful for a cheap test run.",
    )
    args = parser.parse_args()

    load_dotenv()
    try:
        client = anthropic.Anthropic()
    except Exception:
        print("Could not start the Anthropic client.")
        print("Check that .env contains a line like ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    if not DATABASE_PATH.exists():
        print(f"No database found at {DATABASE_PATH}")
        print("Run this first:  python3 src/load_db.py")
        sys.exit(1)

    taxonomy_text, theme_names = read_taxonomy()
    print(f"Taxonomy: {len(theme_names)} themes from {TAXONOMY_PATH}\n")

    tool = build_tool(theme_names)
    system_prompt = build_system_prompt(taxonomy_text)

    connection = sqlite3.connect(DATABASE_PATH)
    # Make SQLite actually enforce the link to the reviews table.
    connection.execute("PRAGMA foreign_keys = ON")

    todo = choose_reviews(connection, args.only_labeled, args.limit)
    if not todo:
        print("\nNothing left to classify.")
        connection.close()
        return

    batches = [todo[i:i + BATCH_SIZE] for i in range(0, len(todo), BATCH_SIZE)]
    print(f"\nSending {len(batches)} requests of up to {BATCH_SIZE} reviews each\n")

    totals = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    classified_count = 0
    failed_reviews = 0

    try:
        for number, batch in enumerate(batches, start=1):
            records = classify_batch(
                client, tool, system_prompt, batch, theme_names, totals
            )

            missed = len(batch) - len(records)
            if missed:
                failed_reviews += missed

            if records:
                save_records(connection, records)
                classified_count += len(records)

            note = f"  ({missed} skipped, logged)" if missed else ""
            print(f"Batch {number:>3} of {len(batches)} | "
                  f"classified {classified_count:,} of {len(todo):,}{note}")

            time.sleep(PAUSE_SECONDS)

    except KeyboardInterrupt:
        print("\n\nStopped by you. Everything classified so far is saved.")

    total_rows = connection.execute(
        "SELECT COUNT(*) FROM classifications").fetchone()[0]
    connection.close()

    print(f"\nClassified this run     {classified_count:,}")
    print(f"Rows in classifications {total_rows:,}")
    if failed_reviews:
        print(f"Reviews not classified  {failed_reviews}  (see {FAILURE_LOG_PATH})")

    report_cost(totals, classified_count)


if __name__ == "__main__":
    main()
