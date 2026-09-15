"""
Step 3: Decide which reviews are worth analysing.

Run it from the project root:
    python3 src/clean.py

Adds two columns to the reviews table:
    is_usable        1 = worth analysing, 0 = not
    unusable_reason  why it was excluded (empty when usable)

Nothing is ever deleted - reviews are only flagged, so you can always look
at what was excluded and change your mind.

Hinglish and Hindi reviews are kept as they are. Nothing is translated.
"""

import sqlite3
import sys
from pathlib import Path


DATABASE_PATH = Path("data/swiggy_reviews.db")

MINIMUM_WORDS = 4

# A review is thrown out only if the WHOLE review is one of these phrases.
# "good app but delivery is always late" is kept, because it says something.
# Capitals, punctuation and emoji are ignored when matching, so "Good.",
# "GOOD" and "good 👍" all match "good".
GENERIC_PHRASES = {
    "good", "nice", "ok", "okay", "best", "super", "superb", "excellent",
    "awesome", "great", "bad", "worst", "average", "fast", "good app",
    "nice app", "very good", "very nice", "very bad", "good service",
    "nice service", "very good app", "very nice app", "good delivery",
    "thanks", "thank you", "love it", "poor service",
}

# The reasons, in the order they are checked. A review that breaks several
# rules is counted once, under the first rule it breaks.
REASONS_IN_ORDER = [
    "empty text",
    "emoji only",
    "generic phrase",
    f"under {MINIMUM_WORDS} words",
    "duplicate text",
]


def has_real_characters(text):
    """
    True if the text contains at least one letter or digit.

    Python's isalnum() understands every writing system, not just English,
    so Devanagari ("सबसे अच्छा") counts as real characters while emoji and
    punctuation do not. This is what keeps Hindi reviews safe.
    """
    return any(character.isalnum() for character in text)


def meaningful_words(text):
    """
    Split into words, ignoring anything that is only emoji or punctuation.

    The word_count column treats an emoji as a word, so "good 👍" looks like
    two words. Here it counts as one, which is what we actually mean.
    """
    return [word for word in text.split() if has_real_characters(word)]


def simplify(text):
    """
    Reduce text to plain lowercase words for comparing against the
    generic phrase list. "Very Good! 👍" becomes "very good".
    """
    characters = [
        character.lower() if character.isalnum() or character.isspace() else " "
        for character in text
    ]
    return " ".join("".join(characters).split())


def duplicate_key(text):
    """Lowercased, tidied text - used to spot the same review twice."""
    return " ".join(text.lower().split())


def find_reason(text, texts_already_seen):
    """
    Return why this review is unusable, or None if it is fine.

    The checks run in the order listed in REASONS_IN_ORDER, and the first
    one that matches wins.
    """
    if not isinstance(text, str) or not text.strip():
        return "empty text"

    if not has_real_characters(text):
        return "emoji only"

    if simplify(text) in GENERIC_PHRASES:
        return "generic phrase"

    if len(meaningful_words(text)) < MINIMUM_WORDS:
        return f"under {MINIMUM_WORDS} words"

    if duplicate_key(text) in texts_already_seen:
        return "duplicate text"

    return None


def add_columns_if_missing(connection):
    """
    Add the two new columns, unless they are already there.

    SQLite has no "ADD COLUMN IF NOT EXISTS", so we look first.
    """
    existing = {row[1] for row in connection.execute("PRAGMA table_info(reviews)")}

    if "is_usable" not in existing:
        connection.execute("ALTER TABLE reviews ADD COLUMN is_usable INTEGER")
        print("Added column: is_usable")

    if "unusable_reason" not in existing:
        connection.execute("ALTER TABLE reviews ADD COLUMN unusable_reason TEXT")
        print("Added column: unusable_reason")


def main():
    if not DATABASE_PATH.exists():
        print(f"No database found at {DATABASE_PATH}")
        print("Run this first:  python3 src/load_db.py")
        sys.exit(1)

    with sqlite3.connect(DATABASE_PATH) as connection:
        add_columns_if_missing(connection)

        # Oldest first, so that when the same text appears twice we keep the
        # original and flag the later copy.
        all_reviews = connection.execute(
            "SELECT review_id, content FROM reviews ORDER BY review_date ASC"
        ).fetchall()

        texts_already_seen = set()
        updates = []
        counts = {reason: 0 for reason in REASONS_IN_ORDER}
        usable_total = 0

        for review_id, content in all_reviews:
            reason = find_reason(content, texts_already_seen)

            if reason is None:
                usable_total += 1
                texts_already_seen.add(duplicate_key(content))
                updates.append((1, None, review_id))
            else:
                counts[reason] += 1
                updates.append((0, reason, review_id))

        connection.executemany(
            "UPDATE reviews SET is_usable = ?, unusable_reason = ? WHERE review_id = ?",
            updates,
        )

    total = len(all_reviews)
    removed = total - usable_total
    share = (usable_total / total * 100) if total else 0

    print()
    print(f"Total reviews    {total:>6,}")
    print(f"Usable           {usable_total:>6,}  ({share:.1f}%)")
    print(f"Removed          {removed:>6,}")
    for reason in REASONS_IN_ORDER:
        print(f"    {reason:<18} {counts[reason]:>6,}")


if __name__ == "__main__":
    main()
