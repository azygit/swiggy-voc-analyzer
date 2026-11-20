# Swiggy Play Store reviews: what customers are telling us

**DRAFT**

**Data:** 15,000 Play Store reviews scraped 12 August – 14 September 2026.
5,287 carried enough text to analyse. Classified by Claude Haiku 4.5 into the
twelve themes in `docs/taxonomy.md`. All figures below come from
`data/outputs/`; those not produced by the main analysis are calculated by
`src/memo_figures.py` and saved in `data/outputs/memo_figures.csv`.

---

## The bottom line

Three problems account for most of the harm customers report, and they are the
same problem seen from three angles: **an order goes wrong, the money does not
come back, and nobody can be reached about it.**

| Rank | Theme | Impact | Reviews | Avg rating | Share at severity 3 |
|---|---|---|---:|---:|---:|
| 1 | Customer support | 36.9 | 747 | 1.07 ★ | 36% |
| 2 | Missing or undelivered order | 32.7 | 548 | 1.12 ★ | **83%** |
| 3 | Refunds and cancellation | 31.7 | 557 | 1.12 ★ | **73%** |
| 4 | Delivery timing | 30.6 | 736 | 1.35 ★ | 12% |
| 5 | Food quality and packaging | 16.5 | 329 | 1.26 ★ | 51% |

Impact = share of reviews × share negative × thumbs-up factor × average severity.
There is a clear break after rank 4: the fifth theme scores roughly half the
fourth.

## Frequency is pointing at the wrong problem

**Delivery timing is the second most common complaint and the fourth most
damaging.** 736 reviews mention it, but only 12% describe losing money or an
order — late food is annoying and recoverable.

Compare that with missing and undelivered orders: fewer reviews (548), but
**83% are severity 3**. The customer paid and got nothing.

If the roadmap were ranked by complaint volume, delivery speed would sit near
the top. Ranked by harm, it sits below three problems that cost people money.
That reordering is the main argument of this memo.

## Customer support is the lowest-rated thing we do

747 reviews mention support, averaging **1.07 stars** — the lowest of any theme
and effectively the floor of the scale. For comparison, the whole usable set
averages 2.09.

Two things are worth separating.

**Support is usually the whole complaint, not an aggravating factor.** 563 of
the 747 support reviews (75%) carry no other theme. People are not mostly saying
"my order was late *and* support was bad" — they are saying support itself was
the failure. Of the 184 that do pair with something else, the commonest partners
are missing orders (70) and delivery timing (51).

*Caveat: the classifier under-applies themes — its recall on Customer support
was 0.54 against the reference labels. True co-occurrence is probably higher
than 25%, so treat the split as indicative, not settled.*

**The bot is named, and never kindly.** 124 reviews mention a chatbot or AI
assistant directly. **99% of them are negative.** That is a small share of total
volume (2.3%) but an unusually clean signal — almost nobody mentions it to say
it helped.

> "worst customer support I have received in my entire life. i have not received
> my order from the last 1.5 hrs and they are just apologizing and not giving me
> any update"

## Nothing is getting worse — which is its own finding

Weekly shares across the five complete weeks are flat:

| Week | Support | Delivery timing | Missing order | Refunds |
|---|---:|---:|---:|---:|
| W32 | 13.9% | 14.2% | 9.9% | 13.1% |
| W33 | 13.5% | 13.5% | 10.9% | 10.6% |
| W34 | 15.3% | 12.7% | 10.9% | 9.4% |
| W35 | 14.5% | 14.8% | 8.7% | 10.6% |
| W36 | 13.8% | 13.8% | 11.8% | 9.5% |

No theme moves more than about two points. These are **chronic conditions, not a
regression** — there is no recent release or incident to point at, and no reason
to expect them to resolve on their own.

App version comparisons show small rises for support and delivery timing in
4.115.1, but newer versions also carry the most recent reviews, so version and
recency cannot be separated in five weeks of data. **Not evidence of a bad
release.**

## What I would do

**1. Guarantee a human for severity-3 cases.** Missing orders and refund
disputes together cover 1,082 reviews, 73–83% of them at severity 3. These are the cases where a bot loop is
most expensive, because the customer has already lost money. Route any "order
not received" or "item missing" contact straight to a person.
*Measure:* share of support-mentioning reviews, and their average rating.

**2. Auto-refund undelivered and missing items below a value threshold.**
Refund friction (557 reviews, 73% severity 3) is a policy choice, not a
technical limit. The recurring story is paying for something that never arrived
and then having to argue for the money.
*Measure:* severity-3 volume in Refunds and cancellation.

**3. Stop charging cancellation fees when the failure is ours.** Reviews
repeatedly describe being charged after cancelling a restaurant-delayed or
never-assigned order. 127 reviews describe being charged for cancelling.
This is small money per order and expensive in trust. (The reviews that
threaten to uninstall point mostly at support, missing orders and refunds,
which is another reason to fix items 1 and 2 first.)
*Measure:* cancellation-fee mentions, and 1-star share.

Delivery speed is deliberately absent. It is the second most frequent
complaint, and I would still not fund it first — it is rarely the thing that
costs a customer their order or their money.

## What this cannot tell you

**Five weeks of data.** Seasonality, festival peaks and year-over-year change
are all invisible. Flat trends over five weeks are not proof of flat trends.

**The sample is deliberately negative.** Cleaning removed very short and
generic reviews ("good", "nice app", emoji only), which were overwhelmingly
positive. The kept reviews average 2.09 stars; the discarded ones average 4.38. This set describes
**customers who explained themselves**, and it is not a measure of overall
satisfaction. Do not quote "75% negative" as a sentiment figure for Swiggy's
customers.

**Play Store reviewers are not customers.** They skew towards people motivated
enough to write, which means the unhappy and the delighted. Nothing here is a
substitute for in-app CSAT or contact-rate data, which Swiggy has and this
analysis does not.

**Accuracy figures measure agreement, not truth.** The classifier was checked
against 200 reference labels produced by Claude Opus 5 and spot-checked by hand
on a random sample of 20 — not hand-labelled throughout. Sentiment agreement
94.5%, theme F1 0.83 micro / 0.77 macro. Where both models are wrong in the same
way, nothing here catches it. See `docs/evaluation.md`.

**The classifier misses themes more than it invents them.** Precision is near
1.00 on most themes while recall runs lower, so theme counts here are more
likely under- than over-stated.
