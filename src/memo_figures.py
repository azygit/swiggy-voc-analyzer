"""
Step 9: Work out the extra numbers quoted in the insights memo.

Run it from the project root:
    python3 src/memo_figures.py

Most memo figures already live in data/outputs/ (made by src/analysis.py).
This script calculates the few that do not - for example "how many support
complaints mention nothing else" - so every number in the memo can be traced
back to a file.

It reads data/outputs/classified_reviews.csv (plus the local database, if
present, for the kept-vs-discarded comparison) and writes
data/outputs/memo_figures.csv. It never calls the LLM and costs nothing.

pandas is used here instead of SQL because the CSV stores themes as text
("Delivery timing; Customer support"), and splitting that text is simpler in
pandas than in SQL.
"""

import sqlite3
from pathlib import Path

import pandas as pd


INPUT_PATH = Path("data/outputs/classified_reviews.csv")
OUTPUT_PATH = Path("data/outputs/memo_figures.csv")
DATABASE_PATH = Path("data/swiggy_reviews.db")

# Words that mean the reviewer is talking about the support chatbot.
# \b means "word boundary", so "bot" matches "the bot" but not "bottle".
CHATBOT_PATTERN = r"\b(?:chat ?bot|bot|ai assistant|automated (?:chat|reply|replies))\b"

# Any mention of being charged for cancelling.
CANCELLATION_FEE_PATTERN = r"cancell?ation (?:fee|charge)|charged? (?:me |us )?(?:for |a )?cancel"


def has_theme(table, theme):
    """True for each review whose theme list includes this theme."""
    return table["theme_list"].apply(lambda themes: theme in themes)


def mentions(table, pattern):
    """True for each review whose text matches the pattern (case ignored)."""
    return table["content"].str.contains(pattern, case=False, regex=True, na=False)


def percent(part, whole):
    return round(100 * part / whole, 1) if whole else 0.0


def main():
    table = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")

    # Turn "A; B" into the list ["A", "B"] so we can count themes per review.
    table["theme_list"] = table["themes"].fillna("").apply(
        lambda text: [theme.strip() for theme in text.split(";") if theme.strip()]
    )

    rows = []  # each entry: (figure name, value, plain-English note)

    # --- Customer support: is it the whole complaint, or one of several? ---
    support = table[has_theme(table, "Customer support")]
    support_only = support[support["theme_list"].str.len() == 1]
    support_with_other = len(support) - len(support_only)
    rows += [
        ("support_reviews", len(support), "Reviews tagged Customer support"),
        ("support_only_reviews", len(support_only), "Customer support is their only theme"),
        ("support_only_percent", percent(len(support_only), len(support)), "Share of support reviews with no other theme"),
        ("support_with_other_theme", support_with_other, "Support reviews that also carry another theme"),
    ]

    # Which themes appear alongside support most often?
    partners = support["theme_list"].explode()
    partners = partners[partners != "Customer support"].value_counts()
    for theme, count in partners.head(3).items():
        rows.append((f"support_paired_with: {theme}", int(count), "Support reviews that also carry this theme"))

    # --- Missing orders and refunds: count each review once ---
    missing = has_theme(table, "Missing or undelivered order")
    refunds = has_theme(table, "Refunds and cancellation")
    rows += [
        ("missing_or_refund_reviews", int((missing | refunds).sum()), "Reviews with either theme, each counted once"),
        ("missing_and_refund_overlap", int((missing & refunds).sum()), "Reviews carrying both themes"),
    ]

    # --- The support chatbot ---
    chatbot = table[mentions(table, CHATBOT_PATTERN)]
    chatbot_negative = (chatbot["sentiment"] == "negative").sum()
    rows += [
        ("chatbot_mentions", len(chatbot), f"Review text matches: {CHATBOT_PATTERN}"),
        ("chatbot_mentions_percent_of_all", percent(len(chatbot), len(table)), "Share of all classified reviews"),
        ("chatbot_negative_percent", percent(chatbot_negative, len(chatbot)), "Share of chatbot mentions classified negative"),
    ]

    # --- Cancellation fees and uninstalling ---
    fee = mentions(table, CANCELLATION_FEE_PATTERN)
    uninstall = mentions(table, r"uninstall")
    rows += [
        ("cancellation_fee_mentions", int(fee.sum()), f"Review text matches: {CANCELLATION_FEE_PATTERN}"),
        ("uninstall_mentions", int(uninstall.sum()), "Review text contains 'uninstall'"),
        ("cancellation_fee_and_uninstall", int((fee & uninstall).sum()), "Reviews mentioning both"),
    ]

    # Which themes do "uninstall" reviews carry most often?
    uninstall_themes = table[uninstall]["theme_list"].explode().value_counts()
    for theme, count in uninstall_themes.head(3).items():
        rows.append((f"uninstall_paired_with: {theme}", int(count), "Uninstall reviews that carry this theme"))

    # --- Kept vs discarded reviews (needs the local database) ---
    # The deployed dashboard has no database, so this part is skipped there.
    if DATABASE_PATH.exists():
        with sqlite3.connect(DATABASE_PATH) as connection:
            query = """
                SELECT is_usable, COUNT(*) AS reviews, ROUND(AVG(rating), 2) AS avg_rating
                FROM reviews
                GROUP BY is_usable
            """
            for is_usable, count, avg_rating in connection.execute(query):
                label = "kept" if is_usable == 1 else "discarded"
                rows += [
                    (f"{label}_reviews", count, "Reviews after cleaning (src/clean.py)"),
                    (f"{label}_avg_rating", avg_rating, "Average star rating"),
                ]

    # dtype=object keeps counts as whole numbers (747, not 747.0)
    output = pd.DataFrame(rows, columns=["figure", "value", "note"], dtype=object)
    output.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(output.to_string(index=False))
    print(f"\nSaved {len(output)} figures to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
