-- ===========================================================================
-- Step 7: Analysis queries for the Swiggy Voice-of-Customer project
--
-- Run these with:  python3 src/analysis.py
-- Each one is also safe to paste into:  sqlite3 data/swiggy_reviews.db
--
-- Every query is separated by a "-- name: something" marker. analysis.py
-- splits the file on those markers, so keep them exactly as they are.
--
-- THE ONE TRICK USED THROUGHOUT: json_each
--
-- The themes column holds a JSON list, for example:
--     ["Delivery timing","Customer support"]
--
-- SQL cannot count inside a list, so json_each unpacks it. Writing
--     FROM classifications c, json_each(c.themes) AS t
-- turns one row holding two themes into two rows holding one theme each,
-- and t.value is that single theme name. Everything else is ordinary SQL.
-- ===========================================================================


-- name: theme_frequency
-- ---------------------------------------------------------------------------
-- How often does each theme appear?
--
-- Line by line:
--   WITH total AS (...)        works out the number of classified reviews once,
--                              so we can turn counts into percentages
--   FROM classifications c,    every classified review...
--        json_each(c.themes)   ...unpacked so each theme is its own row
--   COUNT(*)                   how many reviews carry this theme
--   ROUND(100.0 * ... , 1)     that count as a percentage of all reviews.
--                              100.0 (not 100) forces decimal division -
--                              with plain 100 SQLite would round down to 0.
--   ORDER BY reviews DESC      most common theme first
-- ---------------------------------------------------------------------------
WITH total AS (SELECT COUNT(*) AS n FROM classifications)
SELECT
    t.value                                        AS theme,
    COUNT(*)                                       AS reviews,
    ROUND(100.0 * COUNT(*) / (SELECT n FROM total), 1) AS share_percent
FROM classifications c, json_each(c.themes) AS t
GROUP BY t.value
ORDER BY reviews DESC;


-- name: theme_trend_weekly
-- ---------------------------------------------------------------------------
-- How does each theme move week by week?
--
-- This is the trend query to trust. The scrape covers about five weeks,
-- which gives five real data points per theme.
--
-- Line by line:
--   strftime('%Y-W%W', ...)    turns a date into a week label like 2026-W34.
--                              SQLite has no date type, but our dates are
--                              stored as 'YYYY-MM-DD HH:MM:SS' text, which
--                              strftime understands.
--   weekly_totals              how many reviews there were in each week, so a
--                              theme's share is measured against that week and
--                              not against the whole dataset
--   HAVING week_reviews >= 200 drops the final part-week (only 62 reviews),
--                              which would otherwise look like a huge drop
--   share_percent              the theme's share of that week. Share matters
--                              more than count: if every theme rises, that is
--                              just more reviews, not a worsening problem.
-- ---------------------------------------------------------------------------
WITH weekly_totals AS (
    SELECT strftime('%Y-W%W', r.review_date) AS week,
           COUNT(*) AS week_reviews
    FROM reviews r
    JOIN classifications c ON c.review_id = r.review_id
    GROUP BY week
    HAVING week_reviews >= 200
)
SELECT
    strftime('%Y-W%W', r.review_date)              AS week,
    t.value                                        AS theme,
    COUNT(*)                                       AS reviews,
    w.week_reviews                                 AS reviews_that_week,
    ROUND(100.0 * COUNT(*) / w.week_reviews, 1)    AS share_percent
FROM reviews r
JOIN classifications c ON c.review_id = r.review_id
JOIN weekly_totals w   ON w.week = strftime('%Y-W%W', r.review_date),
     json_each(c.themes) AS t
GROUP BY week, t.value
ORDER BY week, reviews DESC;


-- name: theme_trend_monthly
-- ---------------------------------------------------------------------------
-- The same thing by calendar month.
--
-- Kept because it was asked for, but read it with care: the data only covers
-- 12 August to 14 September, so September is barely half a month. September
-- will always look smaller than August, and that is an artefact of when the
-- reviews were scraped, not a real fall in complaints. Use share_percent,
-- never the raw count, and prefer the weekly query above.
--
--   strftime('%Y-%m', ...)     turns a date into a month label like 2026-09
-- ---------------------------------------------------------------------------
WITH monthly_totals AS (
    SELECT strftime('%Y-%m', r.review_date) AS month,
           COUNT(*) AS month_reviews
    FROM reviews r
    JOIN classifications c ON c.review_id = r.review_id
    GROUP BY month
)
SELECT
    strftime('%Y-%m', r.review_date)               AS month,
    t.value                                        AS theme,
    COUNT(*)                                       AS reviews,
    m.month_reviews                                AS reviews_that_month,
    ROUND(100.0 * COUNT(*) / m.month_reviews, 1)   AS share_percent
FROM reviews r
JOIN classifications c ON c.review_id = r.review_id
JOIN monthly_totals m  ON m.month = strftime('%Y-%m', r.review_date),
     json_each(c.themes) AS t
GROUP BY month, t.value
ORDER BY month, reviews DESC;


-- name: theme_avg_rating
-- ---------------------------------------------------------------------------
-- What star rating goes with each theme?
--
-- Line by line:
--   JOIN reviews r             the star rating lives in reviews, the theme
--                              lives in classifications, so we join them
--   AVG(r.rating)              the average star rating of reviews carrying
--                              this theme
--   AVG(c.severity)            the average severity our classifier assigned
--   ORDER BY avg_rating ASC    worst-rated theme first, since that is the
--                              interesting end
--
-- Worth comparing the two averages. A theme with a low star rating AND low
-- severity is an irritation; low rating AND high severity is a real problem.
-- ---------------------------------------------------------------------------
SELECT
    t.value                        AS theme,
    COUNT(*)                       AS reviews,
    ROUND(AVG(r.rating), 2)        AS avg_rating,
    ROUND(AVG(c.severity), 2)      AS avg_severity,
    ROUND(AVG(r.thumbs_up), 2)     AS avg_thumbs_up
FROM classifications c
JOIN reviews r ON r.review_id = c.review_id,
     json_each(c.themes) AS t
GROUP BY t.value
ORDER BY avg_rating ASC;


-- name: theme_by_business_line
-- ---------------------------------------------------------------------------
-- Which themes belong to which part of the business?
--
-- Line by line:
--   line_totals                how many reviews each business line has, so a
--                              theme's share is measured inside its own line
--   share_of_line_percent      of all Instamart reviews, what share mention
--                              this theme. This is the number to compare
--                              across lines - raw counts just tell you that
--                              Food and General are bigger.
--
-- Note: most reviews do not name a business line, so General is by far the
-- largest group. Dineout has very few reviews, so treat its percentages as
-- noise rather than signal.
-- ---------------------------------------------------------------------------
WITH line_totals AS (
    SELECT business_line, COUNT(*) AS line_reviews
    FROM classifications
    GROUP BY business_line
)
SELECT
    c.business_line                                       AS business_line,
    t.value                                               AS theme,
    COUNT(*)                                              AS reviews,
    l.line_reviews                                        AS reviews_in_line,
    ROUND(100.0 * COUNT(*) / l.line_reviews, 1)           AS share_of_line_percent
FROM classifications c
JOIN line_totals l ON l.business_line = c.business_line,
     json_each(c.themes) AS t
GROUP BY c.business_line, t.value
ORDER BY c.business_line, reviews DESC;


-- name: theme_version_spikes
-- ---------------------------------------------------------------------------
-- Did any theme jump when a new app version shipped?
--
-- This one needs the most care, for two reasons.
--
-- First, version order. You cannot sort version strings alphabetically -
-- '4.9.0' would sort after '4.115.0', which is wrong. You also cannot sort by
-- the date first seen, because older versions are still in use by people who
-- have not updated. So we split '4.115.1' into three numbers and sort by those:
--   substr(v, 1, instr(v,'.') - 1)      everything before the first dot  -> 4
--   substr(v, instr(v,'.') + 1)         everything after it       -> '115.1'
--   then the same trick again on what is left                     -> 115, 1
--   CAST(... AS INTEGER)                so they sort as numbers, not text
--
-- Second, volume. There are 124 different versions in the data and most have
-- only a handful of reviews, where one extra complaint looks like a 100% jump.
--   HAVING version_reviews >= 200       keeps only versions with enough
--                                       reviews for a change to mean anything
--
--   LAG(...) OVER (PARTITION BY theme ORDER BY ...)
--       looks at the previous row for the same theme - that is, the same
--       theme on the previous version - so we can subtract one from the other
--   change_in_share                     positive means the theme grew on this
--                                       version. That is the spike.
-- ---------------------------------------------------------------------------
WITH parsed AS (
    SELECT
        r.review_id,
        r.app_version,
        CAST(substr(r.app_version, 1, instr(r.app_version, '.') - 1) AS INTEGER) AS major,
        CAST(substr(substr(r.app_version, instr(r.app_version, '.') + 1), 1,
                    instr(substr(r.app_version, instr(r.app_version, '.') + 1), '.') - 1
            ) AS INTEGER) AS minor,
        CAST(substr(substr(r.app_version, instr(r.app_version, '.') + 1),
                    instr(substr(r.app_version, instr(r.app_version, '.') + 1), '.') + 1
            ) AS INTEGER) AS patch
    FROM reviews r
    WHERE r.app_version IS NOT NULL
      AND r.app_version LIKE '%.%.%'
),
version_totals AS (
    SELECT p.app_version, p.major, p.minor, p.patch, COUNT(*) AS version_reviews
    FROM parsed p
    JOIN classifications c ON c.review_id = p.review_id
    GROUP BY p.app_version
    HAVING version_reviews >= 200
),
theme_by_version AS (
    SELECT
        v.app_version,
        v.major, v.minor, v.patch,
        t.value                                         AS theme,
        COUNT(*)                                        AS reviews,
        v.version_reviews,
        ROUND(100.0 * COUNT(*) / v.version_reviews, 2)  AS share_percent
    FROM parsed p
    JOIN version_totals v  ON v.app_version = p.app_version
    JOIN classifications c ON c.review_id = p.review_id,
         json_each(c.themes) AS t
    GROUP BY v.app_version, t.value
)
SELECT
    app_version,
    theme,
    reviews,
    version_reviews,
    share_percent,
    LAG(share_percent) OVER (PARTITION BY theme ORDER BY major, minor, patch)
        AS previous_share_percent,
    ROUND(
        share_percent - LAG(share_percent) OVER (
            PARTITION BY theme ORDER BY major, minor, patch
        ), 2
    ) AS change_in_share
FROM theme_by_version
ORDER BY change_in_share DESC NULLS LAST;


-- name: theme_impact_score
-- ---------------------------------------------------------------------------
-- Which themes actually deserve attention first?
--
-- Frequency alone is a poor guide: a theme can be common but trivial, or rare
-- but cost people money. The impact score multiplies four things together:
--
--   share_of_reviews    how much of the feedback this theme is
--   share_negative      how often it comes with negative sentiment
--   thumbs_factor       1 + the average of ln(1 + thumbs_up).
--                       ln(0) is undefined, which is why it is ln(1 + x).
--                       Taking the log stops one review with 2,590 thumbs-up
--                       from drowning out everything else.
--   avg_severity        the average 1-3 severity, so themes that cost people
--                       money outrank themes that are merely annoying
--
-- Each factor is kept in its own column, not just the final score, so you can
-- see WHY a theme ranks where it does rather than trusting one number.
--
-- Honest caveat: 91% of reviews have zero thumbs-up, so thumbs_factor sits
-- near 1.0 for every theme and does very little of the ranking work here.
-- It would matter more on a dataset where voting is common.
-- ---------------------------------------------------------------------------
WITH total AS (SELECT COUNT(*) AS n FROM classifications),
theme_stats AS (
    SELECT
        t.value                                              AS theme,
        COUNT(*)                                             AS reviews,
        1.0 * COUNT(*) / (SELECT n FROM total)               AS share_of_reviews,
        1.0 * SUM(CASE WHEN c.sentiment = 'negative' THEN 1 ELSE 0 END)
              / COUNT(*)                                     AS share_negative,
        1.0 + AVG(ln(1 + r.thumbs_up))                       AS thumbs_factor,
        AVG(c.severity)                                      AS avg_severity
    FROM classifications c
    JOIN reviews r ON r.review_id = c.review_id,
         json_each(c.themes) AS t
    GROUP BY t.value
)
SELECT
    theme,
    reviews,
    ROUND(100.0 * share_of_reviews, 1)  AS share_percent,
    ROUND(100.0 * share_negative, 1)    AS negative_percent,
    ROUND(thumbs_factor, 3)             AS thumbs_factor,
    ROUND(avg_severity, 2)              AS avg_severity,
    ROUND(
        share_of_reviews * share_negative * thumbs_factor * avg_severity * 100,
        3
    ) AS impact_score
FROM theme_stats
ORDER BY impact_score DESC;
