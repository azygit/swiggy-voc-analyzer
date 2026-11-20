"""
Step 8: The Swiggy Voice-of-Customer dashboard.

Run it from the project root:
    streamlit run app/streamlit_app.py

This app reads ONLY the CSV files in data/outputs/ (plus the insights memo,
which is a plain text file). It never opens the database and never calls an
API, so it is safe to deploy anywhere.
"""

import base64
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


OUTPUT_FOLDER = Path("data/outputs")
MEMO_PATH = Path("docs/insights_memo.md")
LOGO_PATH = Path("app/swiggy_logo.png")


# ---------------------------------------------------------------------------
# Colours
#
# Two complete palettes, not one flipped. Colours that are readable on white
# are often unreadable on black, so each mode has its own steps, and both sets
# were checked against their own background for contrast and for colourblind
# separation before being used here. Do not reorder the series lists - the
# order is what keeps neighbouring lines tellable apart.
# ---------------------------------------------------------------------------

THEMES = {
    "dark": {
        "bg": "#14151c",
        "card": "#1c1d26",
        "border": "#2b2c38",
        "text": "#eceaf3",
        "muted": "#9b9aad",
        "grid": "#262733",
        "accent": "#9085e9",
        "series": ["#9085e9", "#d95926", "#199e70", "#c98500", "#d55181"],
    },
    "light": {
        "bg": "#ffffff",
        "card": "#ffffff",
        "border": "#e9e6e2",
        "text": "#16151a",
        "muted": "#6b6a66",
        "grid": "#eeece9",
        "accent": "#eb6834",
        "series": ["#eb6834", "#2a78d6", "#1baf7a", "#4a3aa7", "#e87ba4"],
    },
}

# Sentiment is a state, not a series, so it keeps the same reserved colours in
# both modes. Every chart using them also shows the label, never colour alone.
SENTIMENT_COLOURS = {
    "positive": "#0ca30c",
    "neutral": "#9a9a95",
    "negative": "#d03b3b",
}


def css(theme):
    """The look of the page: dark cards, big numbers, quiet labels."""
    return f"""
    <style>
      .stApp {{ background: {theme['bg']}; }}
      header[data-testid="stHeader"] {{ background: transparent; }}
      .block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1500px; }}

      /* every chart and tile sits in a rounded card */
      div[data-testid="stVerticalBlockBorderWrapper"] {{
          background: {theme['card']};
          border: 1px solid {theme['border']} !important;
          border-radius: 16px;
          padding: 18px 20px 14px 20px;
      }}

      h1, h2, h3, h4 {{ color: {theme['text']} !important; letter-spacing: -0.02em; }}
      .stMarkdown p, label, .stCaption, small {{ color: {theme['muted']} !important; }}

      .kpi-label {{
          color: {theme['muted']}; font-size: 0.78rem; font-weight: 500;
          text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 2px;
      }}
      .kpi-value {{
          color: {theme['text']}; font-size: 2.5rem; font-weight: 650;
          line-height: 1.1; letter-spacing: -0.03em;
          font-variant-numeric: tabular-nums;
      }}
      .kpi-sub {{ color: {theme['muted']}; font-size: 0.8rem; margin-top: 2px; }}

      .section-title {{
          color: {theme['text']}; font-size: 1.0rem; font-weight: 600;
          margin: 0 0 10px 0; letter-spacing: -0.01em;
      }}
      .pill {{
          display: inline-block; background: {theme['accent']}22;
          color: {theme['accent']}; border: 1px solid {theme['accent']}44;
          border-radius: 999px; padding: 3px 11px; font-size: 0.72rem;
          font-weight: 600; letter-spacing: 0.03em;
      }}

      /* sidebar navigation styled as pills rather than radio dots */
      section[data-testid="stSidebar"] {{
          background: {theme['card']}; border-right: 1px solid {theme['border']};
      }}
      section[data-testid="stSidebar"] div[role="radiogroup"] label {{
          background: transparent; border-radius: 10px; padding: 7px 12px;
          margin-bottom: 3px; width: 100%; transition: background 120ms ease;
      }}
      section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
          background: {theme['accent']}14;
      }}
      section[data-testid="stSidebar"] div[role="radiogroup"] label p {{
          color: {theme['text']} !important; font-weight: 500;
      }}

      div[data-testid="stDataFrame"] {{ border-radius: 12px; overflow: hidden; }}
    </style>
    """


# ---------------------------------------------------------------------------
# Loading. @st.cache_data means each file is read once, not on every click.
# ---------------------------------------------------------------------------

@st.cache_data
def load_reviews():
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
    return pd.read_csv(path, encoding="utf-8-sig").iloc[0] if path.exists() else None


@st.cache_data
def load_memo():
    return MEMO_PATH.read_text(encoding="utf-8") if MEMO_PATH.exists() else None


def all_themes(table):
    """Every theme name that appears, most common first."""
    counts = {}
    for themes in table["theme_list"]:
        for theme in themes:
            counts[theme] = counts.get(theme, 0) + 1
    return [theme for theme, _ in sorted(counts.items(), key=lambda kv: -kv[1])]


# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------

def style(figure, theme, height=340, legend=False):
    """One place for chart styling, so every chart matches the page."""
    figure.update_layout(
        height=height,
        margin=dict(l=6, r=6, t=10, b=6),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=theme["muted"], size=12.5),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None,
                    font=dict(color=theme["muted"])),
        hoverlabel=dict(bgcolor=theme["card"], bordercolor=theme["border"],
                        font=dict(color=theme["text"], size=12.5)),
        barcornerradius=5,
    )
    figure.update_xaxes(showgrid=False, linecolor=theme["border"],
                        tickcolor=theme["border"], zeroline=False)
    figure.update_yaxes(gridcolor=theme["grid"], zeroline=False,
                        linecolor="rgba(0,0,0,0)")
    return figure


def sparkline(values, theme, colour=None):
    """A small trend line that sits under a big number."""
    colour = colour or theme["accent"]
    figure = go.Figure(
        go.Scatter(
            y=list(values), mode="lines",
            line=dict(width=2, color=colour, shape="spline"),
            fill="tozeroy", fillcolor=colour + "1f",
            hoverinfo="skip",
        )
    )
    figure.update_layout(
        height=52, margin=dict(l=0, r=0, t=6, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, xaxis=dict(visible=False),
        yaxis=dict(visible=False, rangemode="tozero"),
    )
    return figure


def kpi(column, theme, label, value, sub, spark=None, colour=None):
    """A big-number tile, optionally with a sparkline beneath it."""
    with column:
        with st.container(border=True):
            st.markdown(
                f"<div class='kpi-label'>{label}</div>"
                f"<div class='kpi-value'>{value}</div>"
                f"<div class='kpi-sub'>{sub}</div>",
                unsafe_allow_html=True,
            )
            if spark is not None and len(spark) > 1:
                st.plotly_chart(
                    sparkline(spark, theme, colour),
                    width="stretch",
                    config={"displayModeBar": False},
                )


def title(text, pill=None):
    badge = f"<span class='pill'>{pill}</span>" if pill else ""
    st.markdown(
        f"<div class='section-title'>{text} &nbsp;{badge}</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def page_overview(table, theme):
    if table.empty:
        st.info("No reviews in the chosen date range.")
        return

    weekly = (
        table.set_index("review_date").resample("W")
        .agg(avg_rating=("rating", "mean"),
             reviews=("rating", "size"),
             negative=("sentiment", lambda s: (s == "negative").mean() * 100))
        .reset_index()
    )
    # Drop part-weeks at either end, which would otherwise look like a cliff.
    full_weeks = weekly[weekly["reviews"] >= 200]

    a, b, c, d = st.columns(4)
    kpi(a, theme, "Reviews analysed", f"{len(table):,}",
        f"{table['day'].min():%d %b} – {table['day'].max():%d %b}",
        spark=full_weeks["reviews"])
    kpi(b, theme, "Average rating", f"{table['rating'].mean():.2f}",
        "out of 5 stars", spark=full_weeks["avg_rating"])
    kpi(c, theme, "Negative", f"{(table['sentiment'] == 'negative').mean() * 100:.0f}%",
        "of classified reviews", spark=full_weeks["negative"],
        colour=SENTIMENT_COLOURS["negative"])
    kpi(d, theme, "Severity 3", f"{int((table['severity'] == 3).sum()):,}",
        "lost money or lost order")

    st.markdown("")

    with st.container(border=True):
        title("Average star rating by week")
        if len(full_weeks) >= 2:
            figure = go.Figure(
                go.Scatter(
                    x=full_weeks["review_date"], y=full_weeks["avg_rating"],
                    mode="lines+markers", line=dict(width=2, color=theme["accent"],
                                                    shape="spline"),
                    marker=dict(size=9, color=theme["accent"],
                                line=dict(width=2, color=theme["card"])),
                    fill="tozeroy", fillcolor=theme["accent"] + "1a",
                    hovertemplate="Week of %{x|%d %b}<br>%{y:.2f} stars<extra></extra>",
                )
            )
            figure.update_yaxes(range=[1, 5])
            st.plotly_chart(style(figure, theme, 300), width="stretch",
                            config={"displayModeBar": False})
        else:
            st.caption("Not enough full weeks in this range to draw a trend.")

    left, right = st.columns(2)

    with left:
        with st.container(border=True):
            title("Sentiment")
            counts = table["sentiment"].value_counts()
            figure = go.Figure(
                go.Pie(
                    labels=counts.index, values=counts.values, hole=0.62,
                    marker=dict(
                        colors=[SENTIMENT_COLOURS.get(s, theme["accent"])
                                for s in counts.index],
                        line=dict(color=theme["card"], width=2),
                    ),
                    textinfo="label+percent", textposition="outside",
                    textfont=dict(color=theme["muted"]),
                    hovertemplate="%{label}<br>%{value:,} reviews<extra></extra>",
                    sort=False,
                )
            )
            st.plotly_chart(style(figure, theme, 320), width="stretch",
                            config={"displayModeBar": False})

    with right:
        with st.container(border=True):
            title("Business line")
            counts = table["business_line"].value_counts().sort_values()
            figure = go.Figure(
                go.Bar(
                    x=counts.values, y=counts.index, orientation="h",
                    marker=dict(color=theme["accent"]),
                    text=[f"{v:,}" for v in counts.values],
                    textposition="outside", textfont=dict(color=theme["muted"]),
                    hovertemplate="%{y}<br>%{x:,} reviews<extra></extra>",
                )
            )
            figure.update_xaxes(showticklabels=False, showgrid=False)
            st.plotly_chart(style(figure, theme, 320), width="stretch",
                            config={"displayModeBar": False})
            st.caption(
                "Most reviews name no business line, so General is largest by "
                "design. Dineout has very few reviews - treat it as noise."
            )


def page_themes(table, impact, theme):
    if table.empty:
        st.info("No reviews in the chosen date range.")
        return

    top = impact.sort_values("impact_score", ascending=False).iloc[0]
    a, b, c = st.columns([2, 1, 1])
    kpi(a, theme, "Highest impact theme", top["theme"],
        f"impact score {top['impact_score']:.1f}")
    kpi(b, theme, "Its share", f"{top['share_percent']:.1f}%", "of all reviews")
    kpi(c, theme, "Average severity", f"{top['avg_severity']:.2f}", "out of 3")

    st.markdown("")

    with st.container(border=True):
        title("Themes ranked by impact", pill="whole period")
        ranked = impact.sort_values("impact_score")
        figure = go.Figure(
            go.Bar(
                x=ranked["impact_score"], y=ranked["theme"], orientation="h",
                marker=dict(color=theme["accent"]),
                text=[f"{v:.1f}" for v in ranked["impact_score"]],
                textposition="outside", textfont=dict(color=theme["muted"]),
                customdata=ranked[["reviews", "share_percent",
                                   "negative_percent", "avg_severity"]].values,
                hovertemplate=(
                    "<b>%{y}</b><br>Impact score %{x:.1f}<br>"
                    "%{customdata[0]:,} reviews (%{customdata[1]:.1f}% of all)<br>"
                    "%{customdata[2]:.1f}% negative<br>"
                    "Average severity %{customdata[3]:.2f}<extra></extra>"
                ),
            )
        )
        figure.update_xaxes(showticklabels=False, showgrid=False)
        st.plotly_chart(style(figure, theme, 460), width="stretch",
                        config={"displayModeBar": False})
        st.caption(
            "Impact = share of reviews × share negative × thumbs-up factor × "
            "average severity. Hover a bar for the four parts. This ranking "
            "covers the whole period and ignores the date filter."
        )

    with st.container(border=True):
        title("Theme trend")
        themes_available = all_themes(table)

        picker, period_col = st.columns([3, 1])
        with picker:
            chosen = st.multiselect("Themes to plot", themes_available,
                                    default=themes_available[:3], max_selections=5)
        with period_col:
            period = st.radio("Period", ["Weekly", "Monthly"], horizontal=True)

        if not chosen:
            st.caption("Pick at least one theme.")
            return

        rule = "W" if period == "Weekly" else "ME"
        totals = table.set_index("review_date").resample(rule).size()
        totals = totals[totals >= (200 if period == "Weekly" else 0)]

        figure = go.Figure()
        for index, name in enumerate(chosen):
            matching = table[table["theme_list"].apply(lambda names: name in names)]
            per_period = matching.set_index("review_date").resample(rule).size()
            per_period = per_period.reindex(totals.index, fill_value=0)
            share = (per_period / totals * 100).round(1)
            colour = theme["series"][index % len(theme["series"])]
            figure.add_trace(
                go.Scatter(
                    x=share.index, y=share.values, mode="lines+markers", name=name,
                    line=dict(width=2, color=colour, shape="spline"),
                    marker=dict(size=8, color=colour,
                                line=dict(width=2, color=theme["card"])),
                    hovertemplate=f"<b>{name}</b><br>%{{y:.1f}}%<extra></extra>",
                )
            )
        figure.update_yaxes(title="share of reviews (%)", rangemode="tozero")
        figure.update_layout(hovermode="x unified")
        st.plotly_chart(style(figure, theme, 380, legend=len(chosen) > 1),
                        width="stretch", config={"displayModeBar": False})

        if period == "Monthly":
            st.caption("The data covers 12 August to 14 September only, so "
                       "September is a part month. Weekly is the honest view.")
        else:
            st.caption("Share of that week's reviews, so a busy week does not "
                       "inflate every theme at once.")


def page_drilldown(table, theme):
    if table.empty:
        st.info("No reviews in the chosen date range.")
        return

    with st.container(border=True):
        title("Filters")
        a, b, c = st.columns(3)
        with a:
            theme_choice = st.multiselect("Theme", all_themes(table))
        with b:
            line_choice = st.multiselect(
                "Business line", sorted(table["business_line"].unique()))
        with c:
            ratings = st.multiselect("Star rating", [1, 2, 3, 4, 5])

    filtered = table
    if theme_choice:
        filtered = filtered[filtered["theme_list"].apply(
            lambda names: any(name in names for name in theme_choice))]
    if line_choice:
        filtered = filtered[filtered["business_line"].isin(line_choice)]
    if ratings:
        filtered = filtered[filtered["rating"].isin(ratings)]

    a, b, c = st.columns(3)
    kpi(a, theme, "Matching reviews", f"{len(filtered):,}", "after filters")
    if filtered.empty:
        st.info("Nothing matches those filters.")
        return
    kpi(b, theme, "Average rating", f"{filtered['rating'].mean():.2f}", "out of 5")
    kpi(c, theme, "Negative",
        f"{(filtered['sentiment'] == 'negative').mean() * 100:.0f}%", "of matches")

    st.markdown("")

    shown = filtered.sort_values("review_date", ascending=False).head(300)
    with st.container(border=True):
        title("Matching reviews")
        st.dataframe(
            pd.DataFrame({
                "Date": shown["review_date"].dt.strftime("%d %b"),
                "★": shown["rating"],
                "Sentiment": shown["sentiment"],
                "Sev": shown["severity"],
                "AI summary": shown["summary"],
                "Themes": shown["themes"],
                "Review": shown["content"],
            }),
            width="stretch", hide_index=True, height=520,
        )
        if len(filtered) > len(shown):
            st.caption(f"Showing the {len(shown)} most recent of "
                       f"{len(filtered):,} matches.")
        st.caption("No usernames or profile pictures were ever collected.")


def page_insights():
    memo = load_memo()
    with st.container(border=True):
        if memo:
            st.markdown(memo)
        else:
            title("Insights memo")
            st.info(
                "The memo has not been written yet. It will appear here once "
                "`docs/insights_memo.md` exists (Step 9)."
            )


def footer(theme):
    evaluation = load_evaluation()
    st.markdown("")
    with st.container(border=True):
        if evaluation is not None:
            st.caption(
                "**Method.** Play Store reviews were scraped, cleaned to drop "
                "one-word and duplicate entries, then classified by Claude "
                "Haiku 4.5 into the themes in `docs/taxonomy.md`."
            )
            st.caption(
                f"**Accuracy** (on {evaluation['reviews_compared']} reviews): sentiment "
                f"{evaluation['sentiment_agreement_percent']}%, business line "
                f"{evaluation['business_line_agreement_percent']}%, severity "
                f"{evaluation['severity_agreement_percent']}%, theme F1 "
                f"{evaluation['theme_f1_micro']} micro / "
                f"{evaluation['theme_f1_macro']} macro. The reference labels were "
                f"produced by {evaluation['reference_model']} and "
                f"{evaluation['reference_note']}, so these figures measure agreement "
                "between two models rather than accuracy against human judgement."
            )
        else:
            st.caption("Run `python3 src/evaluate.py` to show accuracy figures here.")


def main():
    # page_icon is the little picture shown on the browser tab.
    # We use the Swiggy logo saved next to this file (app/swiggy_logo.png).
    # page_title is the text shown beside the logo on the browser tab.
    st.set_page_config(page_title="SwiggyVOC",
                       page_icon=str(LOGO_PATH), layout="wide")

    table = load_reviews()
    impact = load_impact()

    with st.sidebar:
        # Logo and name side by side at the top of the sidebar.
        # The picture is turned into text (base64) so it can sit inside HTML.
        logo_text = base64.b64encode(LOGO_PATH.read_bytes()).decode()
        st.markdown(
            "<div style='display:flex;align-items:center;gap:10px;margin-bottom:0.3rem'>"
            f"<img src='data:image/png;base64,{logo_text}' width='36' "
            "style='border-radius:8px' alt='Swiggy logo'>"
            "<span style='font-size:1.5rem;font-weight:700'>SwiggyVOC</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.caption("Play Store review analysis")
        st.markdown("")

        page = st.radio("Page", ["Overview", "Themes", "Drill-down", "Insights"],
                        label_visibility="collapsed")

        st.markdown("---")
        earliest, latest = table["day"].min(), table["day"].max()
        chosen_range = st.date_input("Date range", value=(earliest, latest),
                                     min_value=earliest, max_value=latest)
        st.markdown("---")
        dark_mode = st.toggle("Dark mode", value=True)

    theme = THEMES["dark" if dark_mode else "light"]
    st.markdown(css(theme), unsafe_allow_html=True)

    st.markdown(
        f"<h2 style='color:{theme['text']};margin-bottom:0.1rem;"
        f"letter-spacing:-0.03em'>{page}</h2>"
        f"<p style='color:{theme['muted']};margin-top:0'>"
        f"Swiggy — what customers are actually saying</p>",
        unsafe_allow_html=True,
    )

    # st.date_input returns one date mid-pick, then two once a range is chosen.
    if isinstance(chosen_range, tuple) and len(chosen_range) == 2:
        start, end = chosen_range
        filtered = table[(table["day"] >= start) & (table["day"] <= end)]
    else:
        filtered = table

    if page == "Overview":
        page_overview(filtered, theme)
    elif page == "Themes":
        page_themes(filtered, impact, theme)
    elif page == "Drill-down":
        page_drilldown(filtered, theme)
    else:
        page_insights()

    footer(theme)


if __name__ == "__main__":
    main()
