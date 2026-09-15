"""
Step 7: Run the analysis queries and save the results for the dashboard.

Run it from the project root:
    python3 src/analysis.py

Reads:  sql/queries.sql and data/swiggy_reviews.db
Writes: one CSV per query in data/outputs/
        data/outputs/classified_reviews.csv for the dashboard drill-down

The SQL lives in sql/queries.sql, not in this file, so the queries can be
read and run on their own.
"""

import re
import sqlite3
import sys
from pathlib import Path

import pandas as pd


DATABASE_PATH = Path("data/swiggy_reviews.db")
QUERIES_PATH = Path("sql/queries.sql")
OUTPUT_FOLDER = Path("data/outputs")

# Excel on Mac mangles Hindi and emoji in plain UTF-8, so use the same
# BOM-prefixed encoding as the label files.
FILE_ENCODING = "utf-8-sig"

# How many rows to show on screen per query. The CSV always has everything.
PREVIEW_ROWS = 12


def load_queries():
    """
    Split sql/queries.sql into named queries.

    Each query in the file starts with a line like "-- name: theme_frequency".
    We split on those markers and keep whatever follows as that query.
    """
    if not QUERIES_PATH.exists():
        print(f"No queries found at {QUERIES_PATH}")
        sys.exit(1)

    text = QUERIES_PATH.read_text(encoding="utf-8")
    chunks = re.split(r"^-- name:\s*(\w+)\s*$", text, flags=re.MULTILINE)

    # re.split gives [before, name1, body1, name2, body2, ...]
    queries = {}
    for index in range(1, len(chunks) - 1, 2):
        name = chunks[index].strip()
        body = chunks[index + 1].strip()
        if body:
            queries[name] = body

    if not queries:
        print(f"No '-- name: something' markers found in {QUERIES_PATH}")
        sys.exit(1)

    return queries


def export_classified_reviews(connection):
    """
    One row per classified review, with its labels, for the dashboard.

    No usernames or profile images appear here - they were never collected
    in the first place, so there is nothing to strip out.
    """
    table = pd.read_sql_query(
        """
        SELECT
            r.review_id,
            r.review_date,
            r.rating,
            r.thumbs_up,
            r.app_version,
            r.word_count,
            r.content,
            c.themes        AS themes_json,
            c.sentiment,
            c.business_line,
            c.severity,
            c.summary
        FROM classifications c
        JOIN reviews r ON r.review_id = c.review_id
        ORDER BY r.review_date DESC
        """,
        connection,
    )

    # The themes column is JSON text. A dashboard is easier to filter if the
    # themes are plain text, so turn ["A","B"] into "A; B" and keep both.
    import json
    table["themes"] = table["themes_json"].apply(
        lambda raw: "; ".join(json.loads(raw))
    )
    table = table.drop(columns=["themes_json"])

    path = OUTPUT_FOLDER / "classified_reviews.csv"
    table.to_csv(path, index=False, encoding=FILE_ENCODING)
    return path, len(table)


def main():
    if not DATABASE_PATH.exists():
        print(f"No database found at {DATABASE_PATH}")
        print("Run this first:  python3 src/load_db.py")
        sys.exit(1)

    queries = load_queries()
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    classified_count = connection.execute(
        "SELECT COUNT(*) FROM classifications").fetchone()[0]
    if classified_count == 0:
        print("No classified reviews yet.")
        print("Run this first:  python3 src/classify.py")
        sys.exit(1)

    print(f"Running {len(queries)} queries over {classified_count:,} "
          f"classified reviews\n")

    for name, sql in queries.items():
        print("=" * 72)
        print(name)
        print("=" * 72)

        try:
            result = pd.read_sql_query(sql, connection)
        except Exception as error:
            print(f"  QUERY FAILED: {error}\n")
            continue

        if result.empty:
            print("  (no rows)\n")
            continue

        print(result.head(PREVIEW_ROWS).to_string(index=False))
        if len(result) > PREVIEW_ROWS:
            print(f"  ... {len(result) - PREVIEW_ROWS:,} more rows in the CSV")

        path = OUTPUT_FOLDER / f"{name}.csv"
        result.to_csv(path, index=False, encoding=FILE_ENCODING)
        print(f"\n  saved {len(result):,} rows to {path}\n")

    path, rows = export_classified_reviews(connection)
    connection.close()

    print("=" * 72)
    print(f"Dashboard drill-down file: {path}  ({rows:,} rows)")
    print("Contains no usernames or profile images.")
    print(f"\nAll outputs are in {OUTPUT_FOLDER}/")


if __name__ == "__main__":
    main()
