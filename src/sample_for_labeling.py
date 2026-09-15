"""
Step 4: Pick two samples of reviews - one to label by hand, one to read
through when working out what the themes should be.

Run it from the project root:
    python3 src/sample_for_labeling.py
    python3 src/sample_for_labeling.py --overwrite   # replace existing files

Reads:  usable reviews from data/swiggy_reviews.db
Writes: data/labels/reference_labels.csv   200 reviews, for you to label
        data/labels/discovery_sample.csv   400 reviews, for finding themes

The two samples never share a review. That matters: if you worked out your
themes from the same reviews you later use to grade the LLM, the score would
flatter itself.

Both samples use a fixed random seed, so running this again gives exactly
the same reviews.
"""

import argparse
import sqlite3
import sys
from pathlib import Path

import pandas as pd


DATABASE_PATH = Path("data/swiggy_reviews.db")
LABELS_FOLDER = Path("data/labels")

REFERENCE_PATH = LABELS_FOLDER / "reference_labels.csv"
DISCOVERY_PATH = LABELS_FOLDER / "discovery_sample.csv"

REFERENCE_SIZE = 200
DISCOVERY_SIZE = 400
RATINGS = [1, 2, 3, 4, 5]

RANDOM_SEED = 42

# Excel on Mac mangles Hindi and emoji in a plain UTF-8 file. "utf-8-sig" is
# the same UTF-8 plus three invisible marker bytes at the start that tell
# Excel what it is reading. Google Sheets and pandas treat it identically.
FILE_ENCODING = "utf-8-sig"

# You fill these in by hand in reference_labels.csv. They are created empty.
COLUMNS_TO_LABEL = ["themes", "sentiment", "business_line", "severity", "notes"]


def load_usable_reviews():
    """Read every review marked usable in Step 3."""
    if not DATABASE_PATH.exists():
        print(f"No database found at {DATABASE_PATH}")
        print("Run this first:  python3 src/load_db.py")
        sys.exit(1)

    with sqlite3.connect(DATABASE_PATH) as connection:
        reviews = pd.read_sql_query(
            """
            SELECT review_id, content, rating
            FROM reviews
            WHERE is_usable = 1
            ORDER BY review_id
            """,
            connection,
        )

    if reviews.empty:
        print("No usable reviews found.")
        print("Run this first:  python3 src/clean.py")
        sys.exit(1)

    return reviews


def pick_balanced_sample(reviews, sample_size):
    """
    Take an equal number of reviews from each star rating.

    If a rating has fewer than its share we take all of them, then top up
    from whatever is left so the total still reaches sample_size.
    """
    per_rating = sample_size // len(RATINGS)
    chosen_parts = []

    for rating in RATINGS:
        for_this_rating = reviews[reviews["rating"] == rating]
        how_many = min(per_rating, len(for_this_rating))
        if how_many:
            chosen_parts.append(
                for_this_rating.sample(n=how_many, random_state=RANDOM_SEED)
            )

    chosen = pd.concat(chosen_parts) if chosen_parts else reviews.iloc[0:0]

    # Top up if some ratings did not have enough reviews to give.
    shortfall = sample_size - len(chosen)
    if shortfall > 0:
        leftover = reviews[~reviews["review_id"].isin(chosen["review_id"])]
        if not leftover.empty:
            chosen = pd.concat([
                chosen,
                leftover.sample(
                    n=min(shortfall, len(leftover)), random_state=RANDOM_SEED
                ),
            ])

    # Shuffle, so you are not reading forty complaints in a row - going
    # through them in blocks by rating quietly biases how you judge the next.
    return chosen.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)


def print_rating_breakdown(sample, wanted_per_rating):
    counts = sample["rating"].value_counts()
    for rating in RATINGS:
        got = int(counts.get(rating, 0))
        short = "   <- fewer than wanted" if got < wanted_per_rating else ""
        print(f"    {rating} star  {got:>4}{short}")


def main():
    parser = argparse.ArgumentParser(
        description="Pick reviews to label by hand and reviews for finding themes."
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing files. This deletes any labelling you have done.",
    )
    args = parser.parse_args()

    # Hand-labelling takes hours. Never wipe it by accident.
    already_there = [p for p in (REFERENCE_PATH, DISCOVERY_PATH) if p.exists()]
    if already_there and not args.overwrite:
        for path in already_there:
            print(f"{path} already exists.")
        print("\nNothing was changed, so any labelling you have done is safe.")
        print("If you really do want fresh samples, either move the old files")
        print("somewhere safe first, or run:")
        print("    python3 src/sample_for_labeling.py --overwrite")
        sys.exit(1)

    reviews = load_usable_reviews()
    print(f"Usable reviews available: {len(reviews):,}\n")

    # The reference sample is drawn first and set aside.
    reference = pick_balanced_sample(reviews, REFERENCE_SIZE)

    # The discovery sample is drawn only from what is left over, so the two
    # can never share a review.
    remaining = reviews[~reviews["review_id"].isin(reference["review_id"])]
    discovery = pick_balanced_sample(remaining, DISCOVERY_SIZE)

    # Belt and braces: stop everything if they somehow overlap.
    overlap = set(reference["review_id"]) & set(discovery["review_id"])
    if overlap:
        print(f"Something is wrong: {len(overlap)} reviews appear in both samples.")
        sys.exit(1)

    # Empty columns for you to fill in by hand.
    for column in COLUMNS_TO_LABEL:
        reference[column] = ""

    LABELS_FOLDER.mkdir(parents=True, exist_ok=True)
    reference.to_csv(REFERENCE_PATH, index=False, encoding=FILE_ENCODING)
    discovery.to_csv(DISCOVERY_PATH, index=False, encoding=FILE_ENCODING)

    print(f"{REFERENCE_PATH}  {len(reference)} reviews, for you to label")
    print_rating_breakdown(reference, REFERENCE_SIZE // len(RATINGS))

    print(f"\n{DISCOVERY_PATH}  {len(discovery)} reviews, for finding themes")
    print_rating_breakdown(discovery, DISCOVERY_SIZE // len(RATINGS))

    print(f"\nNo review appears in both samples.")
    print(f"Encoding: {FILE_ENCODING} (opens correctly in Excel and Google Sheets)")


if __name__ == "__main__":
    main()
