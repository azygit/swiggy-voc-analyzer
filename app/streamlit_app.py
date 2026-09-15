"""
Step 8: The Swiggy Voice-of-Customer dashboard.

Run it from the project root:
    streamlit run app/streamlit_app.py

This app reads ONLY the CSV files in data/outputs/ (plus the insights memo,
which is a plain text file). It never opens the database and never calls an
API, so it is safe to deploy anywhere.
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


OUTPUT_FOLDER = Path("data/outputs")
MEMO_PATH = Path("docs/insights_memo.md")

# ---------------------------------------------------------------------------
# Colours. These come from a validated palette - the ordering is what keeps
# the chart readable for colourblind viewers, so do not shuffle it.
# ---------------------------------------------------------------------------
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
BLUE = "#2a78d6"
INK = "#0b0b0b"
INK_SOFT = "#52514e"
GRID = "#e8e8e6"
SURFACE = "#fcfcfb"

# Sentiment is a state, not a series, so it uses the reserved status colours.
# Every chart using them also shows the label, never colour alone.
SENTIMENT_COLOURS = {
    "positive": "#0ca30c",
    "neutral": "#9a9a95",
    "negative": "#d03b3b",
}


# ---------------------------------------------------------------------------
# Loading. @st.cache_data means each file is read once, not on every click.
# ---------------------------------------------------------------------------

@st.cache_data
def load_reviews():
    """Every classified review, one row each."""
    table = pd.read_csv(OUTPUT_FOLDER / "classified_reviews.csv", encoding="utf-8-sig")
    table["review_date"] = pd.to_datetime(table["review_date"])
    table["day"] = table["review_date"].dt.date
    # "Delivery timing; Customer support" -> ["Delivery timing", "Customer support"]
    table["theme_list"] = table["themes"].fillna("").apply(
        lambda text: [part.strip() for part in text.split(";") if part.strip()]
    )
    return table


@st.cache_data
def load_impact():
    return pd.read_csv(OUTPUT_FOLDER / "theme_impact_score.csv", encoding="utf-8-sig")


@st.cache_data
def load_evaluation():
    path = OUTPUT_FOLDER / "evaluation_summary.csv"
    if not path.exists():
        return None
    return pd.read_csv(path, encoding="utf-8-sig").iloc[0]


@st.cache_data
def load_memo():
    if not MEMO_PATH.exists():
        return None
    return MEMO_PATH.read_text(encoding="utf-8")


def all_themes(table):
    """Every theme name that appears, most common first."""
    counts = {}
    for themes in table["theme_list"]:
        for theme in themes:
            counts[theme] = counts.get(theme, 0) + 1
    return [theme for theme, _ in sorted(counts.items(), key=lambda kv: -kv[1])]


def tidy(figure, height=340, legend=False):
    """One place for the chart styling, so every chart looks the same."""
    figure.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=28, b=8),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(color=INK_SOFT, size=13),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
        hoverlabel=dict(bgcolor="white", font_size=13),
        barcornerradius=4,
    )
    figure.update_xaxes(showgrid=False, linecolor=GRID, tickcolor=GRID)
    figure.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    return figure


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def page_overview(table):
    st.subheader("Overview")

    if table.empty:
        st.info("No reviews in the chosen date range.")
        return

    negative_share = (table["sentiment"] == "negative").mean() * 100
    serious = int((table["severity"] == 3).sum())

    a, b, c, d = st.columns(4)
    a.metric("Reviews analysed", f"{len(table):,}")
    b.metric("Average rating", f"{table['rating'].mean():.2f} ★")
    c.metric("Negative", f"{negative_share:.0f}%")
    d.metric("Severity 3 (lost money or order)", f"{serious:,}")

    st.markdown("")

    # --- rating over time -------------------------------------------------
    weekly = (
        table.set_index("review_date")
        .resample("W")
        .agg(avg_rating=("rating", "mean"), reviews=("rating", "size"))
        .reset_index()
    )
    # Drop part-weeks at either end, which would look like a cliff.
    weekly = weekly[weekly["reviews"] >= 200]

    st.markdown("**Average star rating by week**")
    if len(weekly) >= 2:
        figure = go.Figure(
            go.Scatter(
                x=weekly["review_date"], y=weekly["avg_rating"],
                mode="lines+markers",
                line=dict(width=2, color=BLUE),
                marker=dict(size=9, color=BLUE, line=dict(width=2, color=SURFACE)),
                hovertemplate="Week of %{x|%d %b}<br>%{y:.2f} stars<extra></extra>",
            )
        )
        figure.update_yaxes(range=[1, 5], title=None)
        st.plotly_chart(tidy(figure, 300), width='stretch')
    else:
        st.caption("Not enough full weeks in this range to draw a trend.")

    # --- sentiment and business line -------------------------------------
    left, right = st.columns(2)

    with left:
        st.markdown("**Sentiment**")
        counts = table["sentiment"].value_counts()
        figure = go.Figure(
            go.Pie(
                labels=counts.index, values=counts.values, hole=0.58,
                marker=dict(
                    colors=[SENTIMENT_COLOURS.get(s, BLUE) for s in counts.index],
                    line=dict(color=SURFACE, width=2),
                ),
                textinfo="label+percent", textposition="outside",
                hovertemplate="%{label}<br>%{value:,} reviews<extra></extra>",
                sort=False,
            )
        )
        st.plotly_chart(tidy(figure, 320), width='stretch')

    with right:
        st.markdown("**Business line**")
        counts = table["business_line"].value_counts().sort_values()
        figure = go.Figure(
            go.Bar(
                x=counts.values, y=counts.index, orientation="h",
                marker=dict(color=BLUE),
                text=[f"{v:,}" for v in counts.values],
                textposition="outside", textfont=dict(color=INK_SOFT),
                hovertemplate="%{y}<br>%{x:,} reviews<extra></extra>",
            )
        )
        figure.update_xaxes(showticklabels=False, showgrid=False)
        st.plotly_chart(tidy(figure, 320), width='stretch')
        st.caption(
            "Most reviews do not name a business line, so General is largest "
            "by design. Dineout has very few reviews - treat it as noise."
        )


def page_themes(table, impact):
    st.subheader("Themes")

    if table.empty:
        st.info("No reviews in the chosen date range.")
        return

    # --- impact ranking ---------------------------------------------------
    st.markdown("**Themes ranked by impact score**")
    ranked = impact.sort_values("impact_score")
    figure = go.Figure(
        go.Bar(
            x=ranked["impact_score"], y=ranked["theme"], orientation="h",
            marker=dict(color=BLUE),
            text=[f"{v:.1f}" for v in ranked["impact_score"]],
            textposition="outside", textfont=dict(color=INK_SOFT),
            customdata=ranked[
                ["reviews", "share_percent", "negative_percent", "avg_severity"]
            ].values,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Impact score %{x:.1f}<br>"
                "%{customdata[0]:,} reviews (%{customdata[1]:.1f}% of all)<br>"
                "%{customdata[2]:.1f}% negative<br>"
                "Average severity %{customdata[3]:.2f}"
                "<extra></extra>"
            ),
        )
    )
    figure.update_xaxes(showticklabels=False, showgrid=False)
    st.plotly_chart(tidy(figure, 460), width='stretch')
    st.caption(
        "Impact = share of reviews × share negative × thumbs-up factor × average "
        "severity. Hover any bar to see the four parts. This ranking is computed "
        "over the whole period and does not change with the date filter."
    )

    st.markdown("---")

    # --- trend ------------------------------------------------------------
    st.markdown("**Theme trend**")
    themes = all_themes(table)

    controls_left, controls_right = st.columns([3, 1])
    with controls_left:
        chosen = st.multiselect(
            "Themes to plot", themes, default=themes[:3], max_selections=5,
        )
    with controls_right:
        period = st.radio("Period", ["Weekly", "Monthly"], horizontal=True)

    if not chosen:
        st.caption("Pick at least one theme.")
        return

    rule = "W" if period == "Weekly" else "ME"
    totals = table.set_index("review_date").resample(rule).size()
    minimum = 200 if period == "Weekly" else 0
    totals = totals[totals >= minimum]

    figure = go.Figure()
    for index, theme in enumerate(chosen):
        matching = table[table["theme_list"].apply(lambda names: theme in names)]
        per_period = matching.set_index("review_date").resample(rule).size()
        per_period = per_period.reindex(totals.index, fill_value=0)
        share = (per_period / totals * 100).round(1)
        colour = SERIES[index % len(SERIES)]
        figure.add_trace(
            go.Scatter(
                x=share.index, y=share.values, mode="lines+markers", name=theme,
                line=dict(width=2, color=colour),
                marker=dict(size=9, color=colour, line=dict(width=2, color=SURFACE)),
                hovertemplate=f"<b>{theme}</b><br>%{{y:.1f}}% of reviews<extra></extra>",
            )
        )
    figure.update_yaxes(title="share of reviews (%)", rangemode="tozero")
    figure.update_layout(hovermode="x unified")
    st.plotly_chart(tidy(figure, 380, legend=len(chosen) > 1), width='stretch')

    if period == "Monthly":
        st.caption(
            "The data covers 12 August to 14 September only, so September is a "
            "part month. Weekly is the more honest view."
        )
    else:
        st.caption("Share of that week's reviews, so a busy week does not inflate every theme.")


def page_drilldown(table):
    st.subheader("Drill-down")

    if table.empty:
        st.info("No reviews in the chosen date range.")
        return

    a, b, c = st.columns(3)
    with a:
        theme_choice = st.multiselect("Theme", all_themes(table))
    with b:
        line_choice = st.multiselect(
            "Business line", sorted(table["business_line"].unique())
        )
    with c:
        ratings = st.multiselect("Star rating", [1, 2, 3, 4, 5])

    filtered = table
    if theme_choice:
        filtered = filtered[filtered["theme_list"].apply(
            lambda names: any(theme in names for theme in theme_choice)
        )]
    if line_choice:
        filtered = filtered[filtered["business_line"].isin(line_choice)]
    if ratings:
        filtered = filtered[filtered["rating"].isin(ratings)]

    st.markdown(f"**{len(filtered):,} matching reviews**")

    if filtered.empty:
        st.info("Nothing matches those filters.")
        return

    shown = filtered.sort_values("review_date", ascending=False).head(300)

    display = pd.DataFrame({
        "Date": shown["review_date"].dt.strftime("%d %b"),
        "★": shown["rating"],
        "Sentiment": shown["sentiment"],
        "Sev": shown["severity"],
        "AI summary": shown["summary"],
        "Themes": shown["themes"],
        "Review": shown["content"],
    })
    st.dataframe(display, width='stretch', hide_index=True, height=520)

    if len(filtered) > len(shown):
        st.caption(f"Showing the {len(shown)} most recent of {len(filtered):,} matches.")
    st.caption("No usernames or profile pictures were ever collected.")


def page_insights():
    st.subheader("Insights")
    memo = load_memo()
    if memo:
        st.markdown(memo)
    else:
        st.info(
            "The insights memo has not been written yet.\n\n"
            "It will appear here once `docs/insights_memo.md` exists (Step 9)."
        )


def footer():
    st.markdown("---")
    evaluation = load_evaluation()

    if evaluation is not None:
        st.caption(
            f"**Method.** {evaluation['reviews_compared']} reviews were used to check the "
            "classifier. Play Store reviews were scraped, cleaned to remove one-word and "
            "duplicate entries, then classified by Claude Haiku 4.5 into the themes in "
            "`docs/taxonomy.md`."
        )
        st.caption(
            f"**Accuracy.** Sentiment agreement "
            f"{evaluation['sentiment_agreement_percent']}%, business line "
            f"{evaluation['business_line_agreement_percent']}%, severity "
            f"{evaluation['severity_agreement_percent']}%, theme F1 "
            f"{evaluation['theme_f1_micro']} (micro) / {evaluation['theme_f1_macro']} (macro). "
            f"The reference labels were produced by {evaluation['reference_model']} and "
            f"{evaluation['reference_note']} - so these figures measure agreement between "
            "two models, not accuracy against human judgement."
        )
    else:
        st.caption("Run `python3 src/evaluate.py` to show accuracy figures here.")


def main():
    st.set_page_config(page_title="Swiggy Voice of Customer", layout="wide")
    st.title("Swiggy — Voice of Customer")

    table = load_reviews()
    impact = load_impact()

    with st.sidebar:
        st.header("Swiggy VoC")
        page = st.radio("Page", ["Overview", "Themes", "Drill-down", "Insights"])

        st.markdown("---")
        earliest = table["day"].min()
        latest = table["day"].max()
        chosen_range = st.date_input(
            "Date range",
            value=(earliest, latest),
            min_value=earliest,
            max_value=latest,
        )
        st.caption(f"Data covers {earliest:%d %b} to {latest:%d %b %Y}.")

    # st.date_input gives one date while the user is mid-pick, then two.
    if isinstance(chosen_range, tuple) and len(chosen_range) == 2:
        start, end = chosen_range
        filtered = table[(table["day"] >= start) & (table["day"] <= end)]
    else:
        filtered = table

    if page == "Overview":
        page_overview(filtered)
    elif page == "Themes":
        page_themes(filtered, impact)
    elif page == "Drill-down":
        page_drilldown(filtered)
    else:
        page_insights()

    footer()


if __name__ == "__main__":
    main()
