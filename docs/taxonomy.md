# Swiggy VoC Taxonomy

Built by reading all 400 reviews in `data/labels/discovery_sample.csv`.
Every example quote below comes from that file. No quote comes from
`reference_labels.csv` - those 200 reviews are the answer key for Step 6 and
must stay unseen, or the evaluation would be marking its own homework.

Twelve themes. Pick **one primary theme** per review. If a review genuinely
covers two, pick the one that caused the most harm to the customer.

---

## Themes

### 1. Delivery timing
**Definition:** The order arrived late, arrived slowly, or the estimated time
shown in the app was wrong.
**Does NOT include:** Orders that never arrived at all (theme 2), or delays
caused by rider behaviour such as refusing to come to the door (theme 4).
**Example:** *"Swiggy's 6 minutes are about 25-30 minutes on Earth."*

### 2. Missing or undelivered order
**Definition:** The order never arrived, was marked delivered when it was not,
or arrived with items missing or replaced by the wrong ones.
**Does NOT include:** Orders that arrived complete but late (theme 1), or
orders that arrived complete but in poor condition (theme 3).
**Example:** *"Order shown delivered, but it wasn't delivered"*

### 3. Food quality and packaging
**Definition:** The food itself was bad on arrival - cold, stale, spoiled,
unsafe - or the packaging leaked, broke, melted or had been opened.
**Does NOT include:** Complaints that the food was poor *value* for the price
(theme 5), or that items were missing from the bag (theme 2).
**Example:** *"Disgusting food the pizza i ordered was a complete mess it was
smelling so bad"*

### 4. Delivery partner conduct
**Definition:** How the rider behaved - rude or polite, unreachable, refusing
to come to the address, demanding extra money.
**Does NOT include:** The rider simply being late (theme 1), or the app
sending the rider to the wrong place (theme 10).
**Example:** *"sumtime riders r very rude"*

### 5. Pricing and extra charges
**Definition:** The cost is too high - menu prices, delivery fees, packaging
fees, handling fees, surge pricing or taxes.
**Does NOT include:** Cases where the price *changed* or differed from what
was advertised, which is theme 6.
**Example:** *"Every order is charged with 12 rs handling fees, 16 delivery
fee even and rain surge fees"*

### 6. Misleading offers and pricing
**Definition:** What was advertised did not match what was charged - coupons
that fail, offers that do not exist, cashback never credited, or a price that
rises between browsing and checkout.
**Does NOT include:** Prices that are simply high but honestly shown (theme 5).
The distinction is whether the customer feels *misled*, not overcharged.
**Example:** *"Browse the restaurant: 'Free Delivery.' Hit the payment screen:
₹71 delivery fee magically added"*

### 7. Refunds and cancellation
**Definition:** Trouble getting money back or cancelling an order - refunds
refused, partial or paid as coupons, cancellation blocked, cancellation fees.
**Does NOT include:** The original failure that prompted the refund request.
Label a late order that was refunded badly as theme 7 only if the refund is
the main complaint.
**Example:** *"U cant cancel ur order even if u ordered some seconds ago"*

### 8. Customer support
**Definition:** Trouble getting help - chatbots that loop, no way to reach a
human, long waits, agents who do not resolve the issue or blame the restaurant.
**Does NOT include:** The underlying problem the customer contacted support
about. Use this when the *support experience itself* is the complaint.
**Example:** *"Swiggy has no human in the loop, if something goes wrong there
is no way at all to contact anyone"*

### 9. App experience and bugs
**Definition:** The app itself - crashes, tracking that will not load, login
failures, payment methods missing or failing, cluttered design, ads, and
feature requests.
**Does NOT include:** The map putting the pin in the wrong place (theme 10),
or offers failing to apply (theme 6).
**Example:** *"the app auto closes when i click on the current order status tab"*

### 10. Location and address
**Definition:** The app gets the location wrong - inaccurate map pins, address
mismatches, or an address the app refuses to serve.
**Does NOT include:** A rider who had the right address but went elsewhere
(theme 4).
**Example:** *"Swiggy always fetches my delivery location incorrectly; it
usually places the pin on a nearby block"*

### 11. Positive experience
**Definition:** Praise with no specific complaint attached - fast delivery,
good food, good value, a helpful rider, a pleasant app.
**Does NOT include:** Reviews that praise something *and* raise a specific
problem. Those get the problem's theme with `negative` sentiment. "Good app
but the charges are high" is theme 5, not theme 11.
**Example:** *"The order comes so fast my first order came in 5 minutes in
Instamart."*

### 12. Other
**Definition:** Anything the eleven themes above do not cover - unrelated
comments, unclear text, one-off requests.
**Does NOT include:** Reviews that fit a theme awkwardly. Force yourself to
pick a real theme where one applies; `other` is for genuine misfits.
**Example:** *"Where are the certificates for your organic fruits and
vegetables?"*

**Watch the `other` pile.** If it grows past roughly one in ten, a theme is
missing and the taxonomy needs another pass.

---

## Sentiment

| Value | Meaning |
|---|---|
| `positive` | The reviewer is happy |
| `neutral` | A question, a feature request, or no clear feeling |
| `negative` | The reviewer is unhappy |

Some reviews are genuinely both - *"very good service but very slow"*. With
three values and no `mixed` option, the rule is: **if the review names a
specific problem, it is `negative`**, however warmly it opens. Praise alone is
`positive`. This keeps sentiment consistent with the theme rule in 11.

---

## Business line

| Value | Meaning |
|---|---|
| `Food` | Restaurant food delivery |
| `Instamart` | Groceries and quick commerce |
| `Dineout` | Restaurant booking and dining out |
| `General` | Not stated, or about Swiggy as a whole |

Most reviews name no business line, so `General` will be the most common value
by a wide margin. **Use it rather than guessing** - defaulting to `Food` would
quietly inflate its share of the Step 7 analysis. `Dineout` barely appears in
this sample at all; expect very few.

---

## Severity

Severity measures **impact on the customer**, not how angry the writing sounds.
An all-caps rant about a late order is still a 2.

| Level | Meaning | Examples |
|---|---|---|
| **1** | Minor annoyance | "Please add dark mode"; "delivery charges a bit high"; all praise |
| **2** | A real problem | Order an hour late; food arrived cold; support chat went nowhere |
| **3** | Lost money or lost the order | Order never arrived; refund refused; charged after cancelling; unsafe food |

All `positive` reviews are severity `1`.

---

## Labelling rules

1. **Label only what the text says.** Do not infer an unstated cause.
2. **One primary theme per review.** If two apply, pick the one that harmed
   the customer most.
3. **Do not translate.** Hinglish, Hindi, Bengali and Tamil reviews are
   labelled from the text as written.
4. **Comparisons to Zomato, Zepto or Blinkit are not a theme.** Label the
   underlying topic - *"Zomato customer care is far better"* is theme 8.
5. Use `notes` for any call you found hard. Those are exactly the reviews the
   LLM will disagree with you on in Step 6, and you will want to know why.
