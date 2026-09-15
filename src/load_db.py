"""
Step 2: Load the scraped reviews CSV into a SQLite database.

Run it from the project root:
    python3 src/load_db.py

Reads:  the newest data/raw/swiggy_reviews_*.csv
Writes: data/swiggy_reviews.db

Safe to run as many times as you like - reviews already in the database
are skipped, so you never get duplicates.
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

RAW_FOLDER = Path("data/raw")
DATABASE_PATH = Path("data/swiggy_reviews.db")

# The CSV calls the review text "review_text"; the database calls it "content".
# Left side = column name in the CSV, right side = column name in the database.
CSV_TO_DATABASE_NAMES = {
    "review_id": "review_id",
    "review_text": "content",
    "rating": "rating",
    "thumbs_up": "thumbs_up",
    "app_version": "app_version",
    "review_date": "review_date",
}


def find_newest_csv():
    """
    Return the most recent CSV in data/raw, or stop with a helpful message.

    The filenames end in YYYY-MM-DD, so sorting them alphabetically also
    sorts them by date - the last one is the newest.
    """
    csv_files = sorted(RAW_FOLDER.glob("swiggy_reviews_*.csv"))

    if not csv_files:
        print(f"No CSV files found in {RAW_FOLDER}/")
        print("Run this first:  python3 src/scrape.py")
        sys.exit(1)

    return csv_files[-1]


def create_tables(connection):
    """
    Create the two tables and their indexes, if they do not already exist.

    "IF NOT EXISTS" means running this a second time changes nothing,
    rather than complaining that the tables are already there.
    """
    # The reviews themselves. review_id is the PRIMARY KEY, which means
    # SQLite will not allow two rows with the same ID - this is what stops
    # duplicates when the script is re-run.
    connection.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            review_id   TEXT PRIMARY KEY,
            content     TEXT,
            rating      INTEGER,
            thumbs_up   INTEGER,
            app_version TEXT,
            review_date TEXT,
            word_count  INTEGER
        )
    """)

    # Empty for now - Step 5 fills this in with the LLM's answers.
    # Making review_id the primary key here means "already classified"
    # is simply "already in this table", so Step 5 can skip those and
    # never pay to classify the same review twice.
    connection.execute("""
        CREATE TABLE IF NOT EXISTS classifications (
            review_id     TEXT PRIMARY KEY,
            themes        TEXT,
            sentiment     TEXT,
            business_line TEXT,
            severity      INTEGER CHECK (severity BETWEEN 1 AND 3),
            summary       TEXT,
            model         TEXT,
            classified_at TEXT,
            FOREIGN KEY (review_id) REFERENCES reviews (review_id)
        )
    """)

    # Indexes are lookup shortcuts. These two make the Step 7 queries
    # (counting by star rating, and trends over time) much faster.
    connection.execute(
        "CREATE INDEX IF NOT EXISTS index_reviews_rating ON reviews (rating)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS index_reviews_date ON reviews (review_date)"
    )


def count_words(text):
    """Count the words in a review. Blank or missing text counts as 0."""
    if not isinstance(text, str):
        return 0
    return len(text.split())


def prepare_rows(csv_path):
    """Read the CSV and return a list of rows ready to insert."""
    table = pd.read_csv(csv_path)

    # Keep only the columns we want, renamed to their database names.
    table = table[list(CSV_TO_DATABASE_NAMES)].rename(columns=CSV_TO_DATABASE_NAMES)

    # Work out the word count for each review.
    table["word_count"] = table["content"].apply(count_words)

    # pandas uses NaN for empty cells; SQLite wants None instead.
    table = table.astype(object).where(pd.notna(table), None)

    column_order = [
        "review_id", "content", "rating", "thumbs_up",
        "app_version", "review_date", "word_count",
    ]
    return [tuple(row) for row in table[column_order].itertuples(index=False)]


def insert_reviews(connection, rows):
    """
    Insert the rows, skipping any review already in the database.

    "INSERT OR IGNORE" tells SQLite: if this review_id is already there,
    quietly move on instead of raising an error.
    """
    before = connection.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]

    connection.executemany(
        """
        INSERT OR IGNORE INTO reviews
            (review_id, content, rating, thumbs_up,
             app_version, review_date, word_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )

    after = connection.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    added = after - before
    return added, len(rows) - added


def main():
    csv_path = find_newest_csv()
    print(f"Reading  {csv_path}")

    rows = prepare_rows(csv_path)
    print(f"Found    {len(rows):,} reviews in the CSV")

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # "with" makes sure the database is saved and closed properly,
    # even if something goes wrong partway through.
    with sqlite3.connect(DATABASE_PATH) as connection:
        create_tables(connection)
        added, skipped = insert_reviews(connection, rows)

        review_count = connection.execute(
            "SELECT COUNT(*) FROM reviews").fetchone()[0]
        classification_count = connection.execute(
            "SELECT COUNT(*) FROM classifications").fetchone()[0]

    print(f"Added    {added:,} new reviews")
    print(f"Skipped  {skipped:,} already in the database")
    print(f"\nDatabase: {DATABASE_PATH}")
    print(f"  reviews         {review_count:,} rows")
    print(f"  classifications {classification_count:,} rows")


if __name__ == "__main__":
    main()
