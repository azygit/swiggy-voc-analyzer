"""
Step 1: Download Swiggy reviews from the Google Play Store.

Run it from the project root:
    python3 src/scrape.py                 # fetch the default 15,000 reviews
    python3 src/scrape.py --count 200     # small test run first

Saves to: data/raw/swiggy_reviews_<today's date>.csv
"""

import argparse
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd
from google_play_scraper import Sort, reviews


# ---------------------------------------------------------------------------
# Settings. These are the things you might want to change.
# ---------------------------------------------------------------------------

APP_ID = "in.swiggy.android"    # Swiggy's ID on the Play Store
BATCH_SIZE = 200                # how many reviews to ask for at a time
PAUSE_SECONDS = 1.5             # wait between batches, so we don't hammer Google
MAX_RETRIES = 3                 # how many times to retry a batch that fails
RETRY_PAUSE_SECONDS = 5         # wait this long before retrying

OUTPUT_FOLDER = Path("data/raw")

# The only fields we keep, and the friendlier names we give them.
# Everything else the Play Store sends us - including userName and userImage -
# is thrown away and never written to disk.
FIELDS_WE_KEEP = {
    "reviewId": "review_id",
    "content": "review_text",
    "score": "rating",
    "thumbsUpCount": "thumbs_up",
    "reviewCreatedVersion": "app_version",
    "at": "review_date",
}


def keep_only_safe_fields(raw_review):
    """Copy across just the six fields we want, under their new names."""
    return {new_name: raw_review.get(old_name)
            for old_name, new_name in FIELDS_WE_KEEP.items()}


def fetch_one_batch(token):
    """
    Ask the Play Store for one batch of reviews.

    Returns a pair: (list of reviews, token for the next page).
    The token is a bookmark saying "here is where you left off".
    If every retry fails, returns (None, None) so the caller knows to stop.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if token is None:
                # First call: spell out exactly what we want.
                return reviews(
                    APP_ID,
                    lang="en",
                    country="in",
                    sort=Sort.NEWEST,
                    count=BATCH_SIZE,
                )
            # Later calls: the bookmark already remembers those settings.
            return reviews(APP_ID, continuation_token=token)

        except Exception as error:
            print(f"  Batch failed (attempt {attempt} of {MAX_RETRIES}): {error}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_PAUSE_SECONDS)

    return None, None


def save_to_csv(collected_reviews):
    """Write the reviews to a dated CSV file and return the path."""
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    file_path = OUTPUT_FOLDER / f"swiggy_reviews_{date.today()}.csv"
    pd.DataFrame(collected_reviews).to_csv(file_path, index=False)
    return file_path


def main():
    parser = argparse.ArgumentParser(
        description="Download Swiggy reviews from the Google Play Store."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=15000,
        help="How many reviews to fetch (default: 15000).",
    )
    args = parser.parse_args()

    collected_reviews = []   # the reviews we are keeping
    seen_ids = set()         # IDs we already have, so we never store a duplicate
    token = None             # no bookmark yet - we are starting from the top
    batch_number = 0

    print(f"Fetching up to {args.count:,} reviews for {APP_ID}")
    print("Press Ctrl+C at any time to stop and save what has been collected.\n")

    try:
        while len(collected_reviews) < args.count:
            batch_number += 1
            batch, token = fetch_one_batch(token)

            if batch is None:
                print("\nToo many failed attempts in a row. Saving what we have.")
                break

            if not batch:
                print("\nThe Play Store sent back an empty batch - no more reviews.")
                break

            # Keep the new reviews, skipping any we have already seen.
            new_in_this_batch = 0
            for raw_review in batch:
                review_id = raw_review.get("reviewId")
                if review_id in seen_ids:
                    continue
                seen_ids.add(review_id)
                collected_reviews.append(keep_only_safe_fields(raw_review))
                new_in_this_batch += 1

                if len(collected_reviews) >= args.count:
                    break

            print(
                f"Batch {batch_number:>3} | received {len(batch):>3}"
                f" | new {new_in_this_batch:>3}"
                f" | total {len(collected_reviews):,} of {args.count:,}"
            )

            # No bookmark means the Play Store has nothing more to give us.
            if token is None:
                print("\nNo more pages available from the Play Store.")
                break

            time.sleep(PAUSE_SECONDS)

    except KeyboardInterrupt:
        print("\n\nStopped by you. Saving what has been collected so far.")

    if not collected_reviews:
        print("\nNo reviews were collected, so nothing was saved.")
        sys.exit(1)

    file_path = save_to_csv(collected_reviews)

    dates = [r["review_date"] for r in collected_reviews if r["review_date"]]
    print(f"\nSaved {len(collected_reviews):,} reviews to {file_path}")
    if dates:
        print(f"Review dates range from {min(dates).date()} to {max(dates).date()}")


if __name__ == "__main__":
    main()
