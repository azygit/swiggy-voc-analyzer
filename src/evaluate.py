"""
Step 6: Measure how closely Haiku 4.5 agrees with the reference labels.

Run it from the project root:
    python3 src/evaluate.py

Reads:  data/labels/reference_labels.csv   the reference labels
        the classifications table          Haiku's answers for the same 200
Writes: docs/evaluation.md                 the full write-up

Important: the reference labels were produced by Claude Opus 5 and spot-checked
by the project owner on a random sample of 20. This measures agreement between
two models, not accuracy against human ground truth.
"""

import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd


DATABASE_PATH = Path("data/swiggy_reviews.db")
REFERENCE_PATH = Path("data/labels/reference_labels.csv")
TAXONOMY_PATH = Path("docs/taxonomy.md")
OUTPUT_PATH = Path("docs/evaluation.md")

REFERENCE_MODEL = "Claude Opus 5"
SPOT_CHECK_NOTE = "spot-checked by the project owner on a random sample of 20"


def load_both_sets():
    """Read the reference labels and Haiku's answers, lined up by review_id."""
    if not REFERENCE_PATH.exists():
        print(f"No reference labels at {REFERENCE_PATH}")
        sys.exit(1)
    if not DATABASE_PATH.exists():
        print(f"No database at {DATABASE_PATH}")
        sys.exit(1)

    reference = pd.read_csv(REFERENCE_PATH, encoding="utf-8-sig", keep_default_na=False)

    with sqlite3.connect(DATABASE_PATH) as connection:
        predicted = pd.read_sql_query(
            """
            SELECT review_id, themes, sentiment, business_line, severity
            FROM classifications
            """,
            connection,
        )

    merged = reference.merge(
        predicted, on="review_id", how="left", suffixes=("_ref", "_ai")
    )

    missing = merged["themes_ai"].isna().sum()
    if missing:
        print(f"{missing} of the {len(reference)} reference reviews have not been classified.")
        print("Run this first:  python3 src/classify.py --only-labeled")
        sys.exit(1)

    # Reference themes are "A;B" text. Haiku's are a JSON list. Both become sets.
    merged["themes_ref_set"] = merged["themes_ref"].apply(
        lambda text: {part.strip() for part in str(text).split(";") if part.strip()}
    )
    merged["themes_ai_set"] = merged["themes_ai"].apply(
        lambda text: set(json.loads(text))
    )
    merged["severity_ref"] = merged["severity_ref"].astype(int)
    merged["severity_ai"] = merged["severity_ai"].astype(int)

    return merged


def read_theme_names():
    """The twelve theme names, taken from the taxonomy headings."""
    import re
    text = TAXONOMY_PATH.read_text(encoding="utf-8")
    return [name.strip() for name in re.findall(r"^### \d+\. (.+)$", text, re.MULTILINE)]


def simple_accuracy(table, column):
    """How often the two labels match exactly, as a percentage."""
    matches = (table[f"{column}_ref"] == table[f"{column}_ai"]).sum()
    return matches, len(table), matches / len(table) * 100


def confusion_rows(table, column):
    """Count every (reference value, Haiku value) pair that disagreed."""
    pairs = Counter(
        (str(row[f"{column}_ref"]), str(row[f"{column}_ai"]))
        for _, row in table.iterrows()
        if str(row[f"{column}_ref"]) != str(row[f"{column}_ai"])
    )
    return pairs.most_common()


def theme_scores(table, theme_names):
    """
    Precision, recall and F1 for every theme.

    For one theme:
        true positive  - both gave the review this theme
        false positive - only Haiku gave it
        false negative - only the reference gave it
    """
    counts = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})

    for _, row in table.iterrows():
        reference_themes = row["themes_ref_set"]
        haiku_themes = row["themes_ai_set"]
        for theme in theme_names:
            in_reference = theme in reference_themes
            in_haiku = theme in haiku_themes
            if in_reference and in_haiku:
                counts[theme]["tp"] += 1
            elif in_haiku and not in_reference:
                counts[theme]["fp"] += 1
            elif in_reference and not in_haiku:
                counts[theme]["fn"] += 1

    scored = {}
    for theme in theme_names:
        tp = counts[theme]["tp"]
        fp = counts[theme]["fp"]
        fn = counts[theme]["fn"]
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        scored[theme] = {
            "tp": tp, "fp": fp, "fn": fn,
            "precision": precision, "recall": recall, "f1": f1,
            "in_reference": tp + fn, "in_haiku": tp + fp,
        }
    return scored


def overall_scores(scored):
    """
    Two ways of rolling the per-theme scores into one number.

    micro - pool every decision, so common themes dominate
    macro - average the twelve F1 scores equally, so rare themes count the same
    """
    total_tp = sum(s["tp"] for s in scored.values())
    total_fp = sum(s["fp"] for s in scored.values())
    total_fn = sum(s["fn"] for s in scored.values())

    micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    micro_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    micro_f1 = (
        2 * micro_precision * micro_recall / (micro_precision + micro_recall)
        if (micro_precision + micro_recall) else 0.0
    )

    macro_f1 = sum(s["f1"] for s in scored.values()) / len(scored)

    return {
        "tp": total_tp, "fp": total_fp, "fn": total_fn,
        "micro_precision": micro_precision,
        "micro_recall": micro_recall,
        "micro_f1": micro_f1,
        "macro_f1": macro_f1,
    }


def find_disagreements(table):
    """Every review where the two labels differ on any field."""
    rows = []
    for _, row in table.iterrows():
        differences = []
        if row["themes_ref_set"] != row["themes_ai_set"]:
            differences.append("themes")
        if row["sentiment_ref"] != row["sentiment_ai"]:
            differences.append("sentiment")
        if row["business_line_ref"] != row["business_line_ai"]:
            differences.append("business line")
        if row["severity_ref"] != row["severity_ai"]:
            differences.append("severity")
        if differences:
            rows.append((row, differences))
    return rows


def percent(value):
    return f"{value * 100:.1f}%"


def write_report(table, scored, overall, disagreements, theme_names):
    """Write the whole thing out as docs/evaluation.md."""
    total = len(table)
    sent_match, _, sent_pct = simple_accuracy(table, "sentiment")
    biz_match, _, biz_pct = simple_accuracy(table, "business_line")
    sev_match, _, sev_pct = simple_accuracy(table, "severity")
    exact_theme_match = sum(
        1 for _, row in table.iterrows()
        if row["themes_ref_set"] == row["themes_ai_set"]
    )

    lines = []
    add = lines.append

    add("# Step 6: How well does Haiku 4.5 agree with the reference labels?\n")
    add(f"Generated {date.today()} from {total} reviews.\n")

    add("## How to read this, and what it is not\n")
    add(f"The reference labels in `data/labels/reference_labels.csv` were produced by")
    add(f"**{REFERENCE_MODEL}**, and {SPOT_CHECK_NOTE}. They were **not** labelled by")
    add("hand, one review at a time, by a person.\n")
    add("That matters for how you read every number below. This measures **how closely")
    add("two language models agree with each other** - it is not a measurement of")
    add("accuracy against human ground truth. Where the two models happen to be wrong")
    add("in the same way, nothing here will catch it. Where they disagree, it is often")
    add("genuinely unclear which one is right - the disagreement list at the end shows")
    add("several cases where a reasonable person could argue for either label.\n")
    add("A stronger evaluation would use labels written by a person who never saw the")
    add("model's answers. Treat these numbers as a consistency check between a larger")
    add("model and a smaller, cheaper one, which is a useful thing to know but a")
    add("different question from \"is it correct\".\n")

    add("---\n")
    add("## The headline numbers\n")
    add("| Measure | Score | What it means |")
    add("|---|---|---|")
    add(f"| Sentiment agreement | **{sent_pct:.1f}%** | Same sentiment on {sent_match} of {total} reviews |")
    add(f"| Business line agreement | **{biz_pct:.1f}%** | Same business line on {biz_match} of {total} |")
    add(f"| Severity agreement | **{sev_pct:.1f}%** | Same 1-3 severity on {sev_match} of {total} |")
    add(f"| Themes identical | **{exact_theme_match / total * 100:.1f}%** | Exactly the same theme set on {exact_theme_match} of {total} |")
    add(f"| Overall theme F1 (micro) | **{overall['micro_f1']:.3f}** | Headline theme score, see below |")
    add(f"| Overall theme F1 (macro) | **{overall['macro_f1']:.3f}** | Same, but rare themes count equally |")
    add("")

    add("### What precision, recall and F1 mean\n")
    add("Take one theme, say `Delivery timing`.\n")
    add("- **Precision** answers: when Haiku said `Delivery timing`, how often did the")
    add("  reference agree? Low precision means Haiku reaches for the theme too readily.")
    add("- **Recall** answers: of the reviews the reference marked `Delivery timing`,")
    add("  how many did Haiku find? Low recall means Haiku keeps missing it.")
    add("- **F1** combines the two into one number. It stops a theme looking good by")
    add("  being either very cautious or very trigger-happy - you need both to score well.\n")
    add("All three run from 0 to 1, where 1 is perfect agreement.\n")

    add("### Why there are two overall scores\n")
    add("**Micro F1** pools every theme decision across all twelve themes into one")
    add("calculation. Common themes therefore dominate it - it is close to \"how often")
    add("does Haiku get a theme decision right\", weighted by how often each theme occurs.\n")
    add("**Macro F1** works out the F1 for each theme separately and then averages the")
    add("twelve equally. A theme appearing in 3 reviews counts as much as one appearing")
    add("in 45.\n")
    add("**The gap between them is the interesting part.** If micro is much higher than")
    add("macro, the model handles the frequent themes well and struggles with the rare")
    add("ones. That is a normal pattern, and it tells you where the weaknesses are.\n")

    add("---\n")
    add("## Per-theme scores\n")
    add("Sorted by how often the theme appears in the reference labels.\n")
    add("| Theme | In reference | Haiku used | Precision | Recall | F1 |")
    add("|---|---:|---:|---:|---:|---:|")
    for theme in sorted(theme_names, key=lambda t: -scored[t]["in_reference"]):
        s = scored[theme]
        add(f"| {theme} | {s['in_reference']} | {s['in_haiku']} | "
            f"{s['precision']:.2f} | {s['recall']:.2f} | **{s['f1']:.2f}** |")
    add("")
    add(f"Pooled totals: {overall['tp']} agreed, {overall['fp']} applied by Haiku only, "
        f"{overall['fn']} applied by the reference only.\n")

    add("---\n")
    add("## Where the two models disagree on sentiment\n")
    add("Read each row as: the reference said the first value, Haiku said the second.\n")
    sentiment_pairs = confusion_rows(table, "sentiment")
    if sentiment_pairs:
        add("| Reference | Haiku | Count |")
        add("|---|---|---:|")
        for (ref, ai), count in sentiment_pairs:
            add(f"| {ref} | {ai} | {count} |")
    else:
        add("No disagreements.")
    add("")

    add("## Where the two models disagree on business line\n")
    business_pairs = confusion_rows(table, "business_line")
    if business_pairs:
        add("| Reference | Haiku | Count |")
        add("|---|---|---:|")
        for (ref, ai), count in business_pairs:
            add(f"| {ref} | {ai} | {count} |")
    else:
        add("No disagreements.")
    add("")

    add("## Where the two models disagree on severity\n")
    severity_pairs = confusion_rows(table, "severity")
    if severity_pairs:
        add("| Reference | Haiku | Count |")
        add("|---|---|---:|")
        for (ref, ai), count in severity_pairs:
            add(f"| {ref} | {ai} | {count} |")
    else:
        add("No disagreements.")
    add("")

    add("---\n")
    add(f"## Every disagreement ({len(disagreements)} of {total} reviews)\n")
    add("Each entry shows the review, then the two labels. `REF` is the")
    add(f"{REFERENCE_MODEL} label, `AI` is the Haiku 4.5 label.\n")

    for index, (row, differences) in enumerate(disagreements, start=1):
        text = " ".join(str(row["content"]).split())
        add(f"**{index}. Differs on: {', '.join(differences)}** &nbsp; ({row['rating']} star)\n")
        add(f"> {text}\n")
        add(f"- `REF` {' ; '.join(sorted(row['themes_ref_set']))} | "
            f"{row['sentiment_ref']} | {row['business_line_ref']} | sev {row['severity_ref']}")
        add(f"- `AI`&nbsp; {' ; '.join(sorted(row['themes_ai_set']))} | "
            f"{row['sentiment_ai']} | {row['business_line_ai']} | sev {row['severity_ai']}")
        if str(row.get("notes", "")).strip():
            add(f"- Reference note: {row['notes']}")
        add("")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    table = load_both_sets()
    theme_names = read_theme_names()

    scored = theme_scores(table, theme_names)
    overall = overall_scores(scored)
    disagreements = find_disagreements(table)

    write_report(table, scored, overall, disagreements, theme_names)

    total = len(table)
    _, _, sent_pct = simple_accuracy(table, "sentiment")
    _, _, biz_pct = simple_accuracy(table, "business_line")
    _, _, sev_pct = simple_accuracy(table, "severity")

    print(f"Compared {total} reviews\n")
    print(f"Sentiment agreement      {sent_pct:>6.1f}%")
    print(f"Business line agreement  {biz_pct:>6.1f}%")
    print(f"Severity agreement       {sev_pct:>6.1f}%")
    print(f"Theme F1 (micro)         {overall['micro_f1']:>6.3f}")
    print(f"Theme F1 (macro)         {overall['macro_f1']:>6.3f}")
    print(f"\nReviews with any disagreement: {len(disagreements)} of {total}")
    print(f"\nFull write-up saved to {OUTPUT_PATH}")
    print(f"\nNote: reference labels were produced by {REFERENCE_MODEL},")
    print(f"{SPOT_CHECK_NOTE}. This measures model-to-model agreement,")
    print("not accuracy against human ground truth.")


if __name__ == "__main__":
    main()
