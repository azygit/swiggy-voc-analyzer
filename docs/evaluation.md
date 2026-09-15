# Step 6: How well does Haiku 4.5 agree with the reference labels?

Generated 2026-09-15 from 200 reviews.

## How to read this, and what it is not

The reference labels in `data/labels/reference_labels.csv` were produced by
**Claude Opus 5**, and spot-checked by the project owner on a random sample of 20. They were **not** labelled by
hand, one review at a time, by a person.

That matters for how you read every number below. This measures **how closely
two language models agree with each other** - it is not a measurement of
accuracy against human ground truth. Where the two models happen to be wrong
in the same way, nothing here will catch it. Where they disagree, it is often
genuinely unclear which one is right - the disagreement list at the end shows
several cases where a reasonable person could argue for either label.

A stronger evaluation would use labels written by a person who never saw the
model's answers. Treat these numbers as a consistency check between a larger
model and a smaller, cheaper one, which is a useful thing to know but a
different question from "is it correct".

---

## The headline numbers

| Measure | Score | What it means |
|---|---|---|
| Sentiment agreement | **94.5%** | Same sentiment on 189 of 200 reviews |
| Business line agreement | **77.5%** | Same business line on 155 of 200 |
| Severity agreement | **74.5%** | Same 1-3 severity on 149 of 200 |
| Themes identical | **73.0%** | Exactly the same theme set on 146 of 200 |
| Overall theme F1 (micro) | **0.833** | Headline theme score, see below |
| Overall theme F1 (macro) | **0.766** | Same, but rare themes count equally |

### What precision, recall and F1 mean

Take one theme, say `Delivery timing`.

- **Precision** answers: when Haiku said `Delivery timing`, how often did the
  reference agree? Low precision means Haiku reaches for the theme too readily.
- **Recall** answers: of the reviews the reference marked `Delivery timing`,
  how many did Haiku find? Low recall means Haiku keeps missing it.
- **F1** combines the two into one number. It stops a theme looking good by
  being either very cautious or very trigger-happy - you need both to score well.

All three run from 0 to 1, where 1 is perfect agreement.

### Why there are two overall scores

**Micro F1** pools every theme decision across all twelve themes into one
calculation. Common themes therefore dominate it - it is close to "how often
does Haiku get a theme decision right", weighted by how often each theme occurs.

**Macro F1** works out the F1 for each theme separately and then averages the
twelve equally. A theme appearing in 3 reviews counts as much as one appearing
in 45.

**The gap between them is the interesting part.** If micro is much higher than
macro, the model handles the frequent themes well and struggles with the rare
ones. That is a normal pattern, and it tells you where the weaknesses are.

---

## Per-theme scores

Sorted by how often the theme appears in the reference labels.

| Theme | In reference | Haiku used | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| Positive experience | 45 | 47 | 0.96 | 1.00 | **0.98** |
| Pricing and extra charges | 34 | 28 | 0.96 | 0.79 | **0.87** |
| App experience and bugs | 33 | 25 | 1.00 | 0.76 | **0.86** |
| Customer support | 26 | 14 | 1.00 | 0.54 | **0.70** |
| Refunds and cancellation | 24 | 17 | 1.00 | 0.71 | **0.83** |
| Delivery timing | 20 | 17 | 0.94 | 0.80 | **0.86** |
| Misleading offers and pricing | 19 | 13 | 1.00 | 0.68 | **0.81** |
| Other | 14 | 16 | 0.62 | 0.71 | **0.67** |
| Missing or undelivered order | 13 | 10 | 1.00 | 0.77 | **0.87** |
| Food quality and packaging | 11 | 8 | 0.75 | 0.55 | **0.63** |
| Delivery partner conduct | 6 | 3 | 0.67 | 0.33 | **0.44** |
| Location and address | 3 | 3 | 0.67 | 0.67 | **0.67** |

Pooled totals: 187 agreed, 14 applied by Haiku only, 61 applied by the reference only.

---

## Where the two models disagree on sentiment

Read each row as: the reference said the first value, Haiku said the second.

| Reference | Haiku | Count |
|---|---|---:|
| neutral | negative | 4 |
| negative | neutral | 3 |
| neutral | positive | 2 |
| positive | neutral | 1 |
| negative | positive | 1 |

## Where the two models disagree on business line

| Reference | Haiku | Count |
|---|---|---:|
| Food | General | 41 |
| General | Instamart | 2 |
| General | Food | 1 |
| Instamart | Food | 1 |

## Where the two models disagree on severity

| Reference | Haiku | Count |
|---|---|---:|
| 1 | 2 | 40 |
| 2 | 3 | 6 |
| 3 | 2 | 4 |
| 2 | 1 | 1 |

---

## Every disagreement (112 of 200 reviews)

Each entry shows the review, then the two labels. `REF` is the
Claude Opus 5 label, `AI` is the Haiku 4.5 label.

**1. Differs on: themes, business line** &nbsp; (1 star)

> delivery too much delayed guest are gone and delivery boy cut call again and again

- `REF` Delivery partner conduct ; Delivery timing | negative | Food | sev 2
- `AI`&nbsp; Delivery timing | negative | General | sev 2

**2. Differs on: business line** &nbsp; (3 star)

> delivery is always late and much different than the estimated time they show everytime.

- `REF` Delivery timing | negative | Food | sev 2
- `AI`&nbsp; Delivery timing | negative | General | sev 2

**3. Differs on: themes, business line** &nbsp; (2 star)

> apane delivery partner ko delivery bag to dena chahiye vah.. hath me pakad kar thandha khana delivery karte hai..

- `REF` Delivery partner conduct ; Food quality and packaging | negative | Food | sev 2
- `AI`&nbsp; Delivery partner conduct | negative | General | sev 2
- Reference note: no delivery bag so food arrives cold

**4. Differs on: themes, severity** &nbsp; (2 star)

> customer service is very bad .my 2 refunds are still pending.. not satisfied with the services

- `REF` Customer support ; Refunds and cancellation | negative | General | sev 3
- `AI`&nbsp; Refunds and cancellation | negative | General | sev 2

**5. Differs on: severity** &nbsp; (3 star)

> delivery fee is very high otherwise I don't like swiggy

- `REF` Pricing and extra charges | negative | General | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**6. Differs on: business line** &nbsp; (2 star)

> over delivery charges!!!! half biriyani order only 165 but with delivery charges 234 !!!! only 3km 70 rupees charged !!!!!

- `REF` Pricing and extra charges | negative | Food | sev 2
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**7. Differs on: themes** &nbsp; (2 star)

> always fake delulu offers and hidden charges and sometimes rain surge fees is greater than my food value 😑

- `REF` Misleading offers and pricing ; Pricing and extra charges | negative | General | sev 2
- `AI`&nbsp; Misleading offers and pricing | negative | General | sev 2

**8. Differs on: severity** &nbsp; (3 star)

> Restaurant packaging charges are extra too much despite platform fee, delivery fee, gst fee, makes items costly

- `REF` Pricing and extra charges | negative | Food | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | Food | sev 2

**9. Differs on: severity** &nbsp; (2 star)

> very expensive. too much mark up for taxes and delivery charges

- `REF` Pricing and extra charges | negative | General | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**10. Differs on: severity** &nbsp; (4 star)

> everything is ok but are charging too much for delivering

- `REF` Pricing and extra charges | negative | General | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**11. Differs on: themes, severity** &nbsp; (1 star)

> Order was accepted and payment was collected, but later cancelled due to items being out of stock. This seems to be happening frequently, and the chat support was unhelpful in resolving the issue or addressing the inconvenience caused. chat assist by Sufi

- `REF` Customer support ; Refunds and cancellation | negative | General | sev 3
- `AI`&nbsp; Refunds and cancellation | negative | General | sev 2

**12. Differs on: themes, business line** &nbsp; (1 star)

> ₹99 order → ₹222 at checkout. 💀 At this point, I’m not sure if I ordered food or sponsored Swiggy’s entire delivery department. Delivery charges + GST + random fees more than DOUBLED the bill. If a ₹99 order costs ₹222, just show the actual price upfront instead of making customers feel cheated at checkout. Absolutely ridiculous.

- `REF` Misleading offers and pricing ; Pricing and extra charges | negative | Food | sev 2
- `AI`&nbsp; Misleading offers and pricing | negative | General | sev 2

**13. Differs on: severity** &nbsp; (2 star)

> in the description they said it will come in red spicy gravy but its not like that. And curry is little sweet.

- `REF` Food quality and packaging | negative | Food | sev 1
- `AI`&nbsp; Food quality and packaging | negative | Food | sev 2
- Reference note: dish did not match its description

**14. Differs on: business line** &nbsp; (2 star)

> my train food order cancelled and no repayment is there

- `REF` Refunds and cancellation | negative | Food | sev 3
- `AI`&nbsp; Refunds and cancellation | negative | General | sev 3
- Reference note: train catering - no matching business line

**15. Differs on: sentiment** &nbsp; (4 star)

> food quality is good but restuarant should provide some paper plate or something on train delivery atleast

- `REF` Food quality and packaging | neutral | Food | sev 1
- `AI`&nbsp; Food quality and packaging | negative | Food | sev 1
- Reference note: suggestion rather than complaint

**16. Differs on: severity** &nbsp; (4 star)

> it nice but rate is so high please reduce the rate

- `REF` Pricing and extra charges | negative | General | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**17. Differs on: themes, severity** &nbsp; (4 star)

> very confusing address add time

- `REF` App experience and bugs | negative | General | sev 1
- `AI`&nbsp; Location and address | negative | General | sev 2
- Reference note: address entry UI not pin accuracy

**18. Differs on: business line** &nbsp; (5 star)

> very good taste, delicious food

- `REF` Positive experience | positive | Food | sev 1
- `AI`&nbsp; Positive experience | positive | General | sev 1

**19. Differs on: business line** &nbsp; (1 star)

> this has officially become the worst possible app with its delivery charges always being ten times higher. to top it off nowadays their orders are never on time and eventually having to cancel it is the only option.

- `REF` Delivery timing ; Pricing and extra charges | negative | Food | sev 2
- `AI`&nbsp; Delivery timing ; Pricing and extra charges | negative | General | sev 2

**20. Differs on: sentiment** &nbsp; (1 star)

> Not allowing blocking or excluding problematic restaurants. Not allowing negative rating for orders cancelled.

- `REF` App experience and bugs | negative | General | sev 1
- `AI`&nbsp; App experience and bugs | neutral | General | sev 1
- Reference note: feature request framed as complaint

**21. Differs on: severity** &nbsp; (4 star)

> offer is good but taking so many taxes & gst

- `REF` Pricing and extra charges | negative | General | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**22. Differs on: themes, business line** &nbsp; (1 star)

> order kelelya items paiki ardhe missing hote..ani payment adhich kelela hot.. helpline la contact Karun hi refund milala Nahi missing itemcha.. faltu service ahe

- `REF` Missing or undelivered order ; Refunds and cancellation | negative | Food | sev 3
- `AI`&nbsp; Missing or undelivered order | negative | General | sev 3
- Reference note: Marathi - half items missing and no refund

**23. Differs on: themes, severity** &nbsp; (1 star)

> bhai kyaa hai ye itna bekar maine pizza mangaya ye log pratha de diye thode pagal wagal hai kyaa ye

- `REF` Missing or undelivered order | negative | Food | sev 3
- `AI`&nbsp; Food quality and packaging | negative | Food | sev 2
- Reference note: ordered pizza received paratha

**24. Differs on: severity** &nbsp; (4 star)

> the price and offers chance every time

- `REF` Misleading offers and pricing | negative | General | sev 1
- `AI`&nbsp; Misleading offers and pricing | negative | General | sev 2

**25. Differs on: business line, severity** &nbsp; (3 star)

> out of stock products. battery drain and unwanted notifications

- `REF` App experience and bugs | negative | General | sev 1
- `AI`&nbsp; App experience and bugs | negative | Instamart | sev 2
- Reference note: three unrelated minor issues

**26. Differs on: business line** &nbsp; (1 star)

> restaurant close but no refund fraud swingy no download ur money waste Zomato best fraud swiggy fraud swiggy fraud swiggy pls don't download swiggy only best Zomato

- `REF` Refunds and cancellation | negative | Food | sev 3
- `AI`&nbsp; Refunds and cancellation | negative | General | sev 3

**27. Differs on: themes, sentiment** &nbsp; (2 star)

> thk tha but utna aacha ni tha

- `REF` Other | neutral | General | sev 1
- `AI`&nbsp; Food quality and packaging | negative | General | sev 1
- Reference note: vague - no specific issue named

**28. Differs on: themes** &nbsp; (4 star)

> nice but no quick order

- `REF` App experience and bugs | neutral | General | sev 1
- `AI`&nbsp; Other | neutral | General | sev 1
- Reference note: unclear feature request

**29. Differs on: themes, business line** &nbsp; (3 star)

> all good but you ought to mention weather the chicken is halal or not for hassle free consultations

- `REF` App experience and bugs | neutral | Food | sev 1
- `AI`&nbsp; Other | neutral | General | sev 1
- Reference note: halal labelling request

**30. Differs on: themes, business line, severity** &nbsp; (1 star)

> Very disappointing customer support. I reported a genuine quantity issue with my order, but instead of properly resolving it, I received the same generic response saying that a refund cannot be processed. This has happened multiple times. Swiggy needs to improve its customer support and actually investigate genuine complaints instead of sending repetitive template replies. Very disappointed with the service.

- `REF` Customer support ; Refunds and cancellation | negative | Food | sev 3
- `AI`&nbsp; Customer support | negative | General | sev 2

**31. Differs on: themes** &nbsp; (1 star)

> Pathetic customer support! My friend ordered a Tandoori Pizza and received a cheap Corn Pizza instead. Swiggy support didn't offer any refund or proper resolution, and even in response to the complaint, they haven't given any refund yet. Charging full money for wrong orders and zero accountability! Uninstalling Swiggy! 😡👎

- `REF` Customer support ; Missing or undelivered order ; Refunds and cancellation | negative | Food | sev 3
- `AI`&nbsp; Missing or undelivered order | negative | Food | sev 3

**32. Differs on: themes** &nbsp; (1 star)

> best app for food and grocery delivery! just one recommendation i.e reduce handling and packaging costs and bring moar instant discount offers to attract moar new swig patrons! new prob I cannot access the help and support section of the app now it says something is broken pls refresh and try again later if I try to access pls fix it immediately it is happening for all orders current and delivered ones

- `REF` App experience and bugs ; Pricing and extra charges | negative | General | sev 2
- `AI`&nbsp; App experience and bugs | negative | General | sev 2
- Reference note: praise plus broken help section - 1 star

**33. Differs on: severity** &nbsp; (3 star)

> delivery charges is too high

- `REF` Pricing and extra charges | negative | General | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**34. Differs on: business line, severity** &nbsp; (3 star)

> food is delicious but the delivery charges are high 😐

- `REF` Pricing and extra charges | negative | Food | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**35. Differs on: sentiment** &nbsp; (4 star)

> pls simply the landing page UI ... it has unnecessary too many options

- `REF` App experience and bugs | neutral | General | sev 1
- `AI`&nbsp; App experience and bugs | negative | General | sev 1
- Reference note: suggestion

**36. Differs on: business line** &nbsp; (4 star)

> always req with out onion garlic

- `REF` Other | neutral | Food | sev 1
- `AI`&nbsp; Other | neutral | General | sev 1
- Reference note: unclear request

**37. Differs on: business line** &nbsp; (2 star)

> No good experience in Dilvery experience but good quality food

- `REF` Delivery timing | negative | Food | sev 2
- `AI`&nbsp; Delivery timing | negative | General | sev 2
- Reference note: delivery complaint unspecified - timing assumed

**38. Differs on: themes, severity** &nbsp; (3 star)

> cash on dilevery is not applicable at each n every order very disappointing

- `REF` App experience and bugs | negative | General | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**39. Differs on: themes** &nbsp; (3 star)

> The service has evolved a lot since many years. In the name of personalisation, the products and their pricing changes so frequently that you can keep some item in the cart to order later. The ₹1 and ₹9 offers vanish suddenly in the same session. Might be either due to personalisation based on items added to cart or could be due to bugs. Still a long way to go for a stable app. And for once, decide if you want to run delivery business or just bombard many annoying Ads in the delivery screen.

- `REF` App experience and bugs ; Misleading offers and pricing | negative | General | sev 2
- `AI`&nbsp; App experience and bugs | negative | General | sev 2

**40. Differs on: themes, business line, severity** &nbsp; (1 star)

> I ordered food over an hour ago, and I'm only receiving AI chat responses. I haven't been connected to a human agent at all till I had to wait extra 30 mins. This has been a terrible customer service experience.deleted the app can't trust Swiggy anymore

- `REF` Customer support ; Delivery timing | negative | Food | sev 2
- `AI`&nbsp; Customer support | negative | General | sev 3

**41. Differs on: themes, business line** &nbsp; (4 star)

> last order was incomplete and even after repeated complaints refund has not been issued yet

- `REF` Missing or undelivered order ; Refunds and cancellation | negative | Food | sev 3
- `AI`&nbsp; Refunds and cancellation | negative | General | sev 3
- Reference note: 4 stars despite unresolved refund

**42. Differs on: severity** &nbsp; (3 star)

> menyu nahi dikhate ho

- `REF` App experience and bugs | negative | General | sev 1
- `AI`&nbsp; App experience and bugs | negative | General | sev 2

**43. Differs on: severity** &nbsp; (1 star)

> Not possible zero rating, Order not cancelled any condition not interested with Swiggy

- `REF` Refunds and cancellation | negative | General | sev 2
- `AI`&nbsp; Refunds and cancellation | negative | General | sev 3

**44. Differs on: business line** &nbsp; (2 star)

> poor delivery not in given time

- `REF` Delivery timing | negative | Food | sev 2
- `AI`&nbsp; Delivery timing | negative | General | sev 2

**45. Differs on: severity** &nbsp; (5 star)

> would suggest for grocery items but prices are high in food. additional charges other than delivery, GST and handling charge is applied

- `REF` Pricing and extra charges | negative | General | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2
- Reference note: 5 stars with a pricing complaint

**46. Differs on: severity** &nbsp; (1 star)

> Not happy with cash back offers

- `REF` Misleading offers and pricing | negative | General | sev 1
- `AI`&nbsp; Misleading offers and pricing | negative | General | sev 2
- Reference note: offers weak not misleading - taxonomy gap

**47. Differs on: severity** &nbsp; (2 star)

> taking too many extra charges saying "gst and other charges "

- `REF` Pricing and extra charges | negative | General | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**48. Differs on: themes** &nbsp; (1 star)

> bekar he paisha lutne ka kama he 100 ke jagame 500 leta he 😡😡😡😡😡😡bekar

- `REF` Misleading offers and pricing ; Pricing and extra charges | negative | General | sev 2
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**49. Differs on: themes** &nbsp; (3 star)

> My Account is debited but the order is not placed. The customer care number is not working. what can I do?

- `REF` App experience and bugs ; Customer support | negative | General | sev 3
- `AI`&nbsp; Customer support | negative | General | sev 3
- Reference note: money debited with no order placed

**50. Differs on: business line** &nbsp; (1 star)

> Your map feature has some major issue. I ordered from a location that was 15 mins away because it was urgent. The delivery person has been sent off on a wild goose chase in the opposite direction, 30 mins away. This is despite the fact that the selected address is the correct one. Quite disappointed.

- `REF` Location and address | negative | Food | sev 2
- `AI`&nbsp; Location and address | negative | General | sev 2

**51. Differs on: themes, business line** &nbsp; (1 star)

> I accidentally paid twice for a single order because the app didn't show the first payment, so I made the payment again. Later, I discovered that two orders had actually been placed. When I contacted customer support to explain the situation and asked them to cancel one of the orders, they told me I would have to pay the full cancellation fee of ₹200—even though it wasn't my fault at all.

- `REF` App experience and bugs ; Refunds and cancellation | negative | Food | sev 3
- `AI`&nbsp; Refunds and cancellation | negative | General | sev 3

**52. Differs on: business line** &nbsp; (4 star)

> the best app for snack , cravings and food and fast delivery 👍🏼

- `REF` Positive experience | positive | General | sev 1
- `AI`&nbsp; Positive experience | positive | Food | sev 1

**53. Differs on: themes, business line** &nbsp; (1 star)

> worst experience ever I wait for 1 hour just to get my order cancelled that too isnt happening due to restrictions of its ai

- `REF` Customer support ; Refunds and cancellation | negative | Food | sev 3
- `AI`&nbsp; Refunds and cancellation | negative | General | sev 3

**54. Differs on: business line, severity** &nbsp; (4 star)

> kabhi achha pizza de dete he to kabhi kabhi bahut hi kharab kismat ajmao

- `REF` Food quality and packaging | negative | Food | sev 1
- `AI`&nbsp; Food quality and packaging | negative | General | sev 2
- Reference note: Hinglish - inconsistent food quality

**55. Differs on: business line** &nbsp; (2 star)

> unreliable. orders don't get delivered on time.

- `REF` Delivery timing | negative | Food | sev 2
- `AI`&nbsp; Delivery timing | negative | General | sev 2

**56. Differs on: sentiment, business line** &nbsp; (3 star)

> Delivery delayed may be more orders and popular

- `REF` Delivery timing | negative | Food | sev 1
- `AI`&nbsp; Delivery timing | neutral | General | sev 1
- Reference note: reviewer excuses the delay

**57. Differs on: themes** &nbsp; (1 star)

> the worst app I ever use, I have been sitting hungry for half an hour, now the delivery boy is standing two streets away from my house saying that he has reached the location, meanwhile I ordered the food using my live location, when I told him that he will come to my original location, he said that your house is far away.. I called the helpline, they cancelled my order as a solution I will never use this app again

- `REF` Delivery partner conduct ; Location and address ; Refunds and cancellation | negative | Food | sev 3
- `AI`&nbsp; Location and address | negative | Food | sev 3
- Reference note: rider refused to complete delivery

**58. Differs on: themes, business line** &nbsp; (2 star)

> NEVER ORDERING FROM SWIGGY AGAIN. DELAYED MY ORDER BY 15 MINS. NO REFUNDS WERE GIVEN. CUSTOMER CARE ONLY BOTS ANSWER. AND THERE WAS NO RESPONSE FROM THE CUSTOMER CARE. LOST MY 329 RUPEES.

- `REF` Customer support ; Delivery timing ; Refunds and cancellation | negative | Food | sev 3
- `AI`&nbsp; Customer support | negative | General | sev 3

**59. Differs on: severity** &nbsp; (4 star)

> sari app che pan charge vadhare che

- `REF` Pricing and extra charges | negative | General | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2
- Reference note: Gujarati - app fine but charges high

**60. Differs on: themes** &nbsp; (2 star)

> You guys are collecting handling fee extra but some of the products like ice cream and milk packed items and all delivered by broken or leakages. Delivery Men's are rude

- `REF` Delivery partner conduct ; Food quality and packaging ; Pricing and extra charges | negative | Instamart | sev 2
- `AI`&nbsp; Delivery partner conduct | negative | Instamart | sev 2

**61. Differs on: themes** &nbsp; (2 star)

> Why is the rain fee applied there hasn't been a single drop of downpour all day, it feels like cheating when these things happen..

- `REF` Misleading offers and pricing ; Pricing and extra charges | negative | General | sev 2
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**62. Differs on: themes, business line** &nbsp; (1 star)

> Chor hai saale, order kiya item missing aaya fir na hi issue resolve na hua kuch.

- `REF` Customer support ; Missing or undelivered order | negative | Food | sev 3
- `AI`&nbsp; Missing or undelivered order | negative | General | sev 3
- Reference note: Hinglish - item missing and unresolved

**63. Differs on: severity** &nbsp; (2 star)

> it's ok but Sume time chiting

- `REF` Misleading offers and pricing | negative | General | sev 1
- `AI`&nbsp; Misleading offers and pricing | negative | General | sev 2
- Reference note: vague cheating claim

**64. Differs on: themes, business line** &nbsp; (3 star)

> The app works well but delivery partners are not good they mark as delivered but the order was not received I faced this situation twice and there is so much headache for talking to customer care and getting refund or cancel the order. I am going to delete this app just because of delivery people.

- `REF` Customer support ; Delivery partner conduct ; Missing or undelivered order | negative | Food | sev 3
- `AI`&nbsp; Missing or undelivered order | negative | General | sev 3

**65. Differs on: business line** &nbsp; (4 star)

> Ordering food is good.

- `REF` Positive experience | positive | Food | sev 1
- `AI`&nbsp; Positive experience | positive | General | sev 1

**66. Differs on: themes, business line** &nbsp; (1 star)

> Customer support is so pathetic. The food is mostly delayed. Would anyday prefer Zomato over Swiggy.

- `REF` Customer support ; Delivery timing | negative | Food | sev 2
- `AI`&nbsp; Customer support | negative | General | sev 2

**67. Differs on: themes, business line, severity** &nbsp; (1 star)

> Worst service!! Swiggy stores failed to properly maintain consuming products Quality!! Authorities should focus on Quality control. Swiggy Customer care is the worst.. unprofessional back team..

- `REF` Customer support ; Food quality and packaging | negative | Instamart | sev 2
- `AI`&nbsp; Food quality and packaging | negative | Food | sev 3
- Reference note: Swiggy stores implies Instamart

**68. Differs on: business line, severity** &nbsp; (3 star)

> The Swiggy clocks tick slowly. I just observed that when 4 minutes was over as per my clock, Swiggy's clock showed just 1 min less. And then in the end it will show that the food was delivered on time.

- `REF` Delivery timing | negative | Food | sev 1
- `AI`&nbsp; Delivery timing | negative | General | sev 2
- Reference note: claims ETA timer is manipulated

**69. Differs on: business line** &nbsp; (1 star)

> the service of this app is very poor not satisfied with the delivery pick and order process I have ordered at 6:30 pm but it is 8:52 pm right now but the delivery is not done yet if I can give the negative points then I will definitely give -5 stars even I will not going to download this app again

- `REF` Delivery timing | negative | Food | sev 2
- `AI`&nbsp; Delivery timing | negative | General | sev 2
- Reference note: still undelivered when written - borderline theme 2

**70. Differs on: business line** &nbsp; (5 star)

> the 99 store offer is too good , and this is not a paid promotion

- `REF` Positive experience | positive | General | sev 1
- `AI`&nbsp; Positive experience | positive | Instamart | sev 1

**71. Differs on: themes, severity** &nbsp; (2 star)

> service charges very high, not available near by location shops,

- `REF` Location and address ; Pricing and extra charges | negative | General | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**72. Differs on: severity** &nbsp; (3 star)

> dilevery is so slow

- `REF` Delivery timing | negative | General | sev 1
- `AI`&nbsp; Delivery timing | negative | General | sev 2

**73. Differs on: severity** &nbsp; (4 star)

> it's good but some time the quality of food is too bad sorry for that but please make it better

- `REF` Food quality and packaging | negative | Food | sev 1
- `AI`&nbsp; Food quality and packaging | negative | Food | sev 2

**74. Differs on: severity** &nbsp; (2 star)

> charging more as comparetively with the shop

- `REF` Pricing and extra charges | negative | General | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**75. Differs on: themes, severity** &nbsp; (4 star)

> very poor app interface and pathetic customer service. Edit: Got resolution from the Grievance cell of Swiggy.

- `REF` App experience and bugs ; Customer support | negative | General | sev 1
- `AI`&nbsp; Customer support | negative | General | sev 2
- Reference note: edited after issue was resolved

**76. Differs on: themes** &nbsp; (1 star)

> don't buy from them if you contact their customer care they will abuse you and cut the call . supervisors don't respond they will cut call and frame you 💯

- `REF` Customer support | negative | General | sev 2
- `AI`&nbsp; Delivery partner conduct | negative | General | sev 2

**77. Differs on: themes, sentiment, business line, severity** &nbsp; (3 star)

> same restaurant with different names why ?‽

- `REF` Other | neutral | Food | sev 1
- `AI`&nbsp; Delivery timing | negative | General | sev 2
- Reference note: duplicate restaurant listings question

**78. Differs on: sentiment, severity** &nbsp; (5 star)

> thanks for resolving the issue. hope to get refund soon.

- `REF` Refunds and cancellation | positive | General | sev 1
- `AI`&nbsp; Refunds and cancellation | neutral | General | sev 2
- Reference note: thanks but refund still pending - hard call

**79. Differs on: business line** &nbsp; (5 star)

> good service and food

- `REF` Positive experience | positive | Food | sev 1
- `AI`&nbsp; Positive experience | positive | General | sev 1

**80. Differs on: severity** &nbsp; (3 star)

> Please have a human intervention customer support to be connected directly. Other than that I love everything.

- `REF` Customer support | negative | General | sev 1
- `AI`&nbsp; Customer support | negative | General | sev 2
- Reference note: praise plus one support request

**81. Differs on: business line** &nbsp; (1 star)

> worst food delivery app...Zomato is far better...They don't deliver food even after 2 hours...Worst...They just show assigning as priority

- `REF` Delivery timing | negative | Food | sev 2
- `AI`&nbsp; Delivery timing | negative | General | sev 2

**82. Differs on: themes, severity** &nbsp; (1 star)

> The worst and fraudulent app that loots money . no proper customer response.. unsafe delivery partners

- `REF` Customer support ; Delivery partner conduct ; Misleading offers and pricing | negative | General | sev 2
- `AI`&nbsp; Customer support | negative | General | sev 3
- Reference note: general rant spanning themes

**83. Differs on: business line, severity** &nbsp; (3 star)

> Why are menu prices higher on the app than at the restaurant one orders from. Ideally you should charge the same menu rate plus your delivery charges. Currently it seems Swiggy is a reseller ?

- `REF` Pricing and extra charges | negative | Food | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**84. Differs on: severity** &nbsp; (3 star)

> delivery time is more

- `REF` Delivery timing | negative | General | sev 1
- `AI`&nbsp; Delivery timing | negative | General | sev 2

**85. Differs on: severity** &nbsp; (3 star)

> if i place an order i forgot to modify my order it said we can't do this

- `REF` App experience and bugs | negative | General | sev 1
- `AI`&nbsp; App experience and bugs | negative | General | sev 2
- Reference note: order modification not possible

**86. Differs on: themes** &nbsp; (5 star)

> bring more new attractive offers & deals @value4money

- `REF` Misleading offers and pricing | neutral | General | sev 1
- `AI`&nbsp; Other | neutral | General | sev 1
- Reference note: request for better offers - taxonomy gap

**87. Differs on: severity** &nbsp; (2 star)

> all food rates too high... including tax, package charge etc...

- `REF` Pricing and extra charges | negative | Food | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | Food | sev 2

**88. Differs on: themes, sentiment, severity** &nbsp; (1 star)

> not Delivered On The Time

- `REF` Delivery timing | negative | General | sev 2
- `AI`&nbsp; Other | neutral | General | sev 1

**89. Differs on: severity** &nbsp; (2 star)

> Everything is handled by a Swiggy bot these days. If I want to cancel an order, modify it, or resolve any issue, there seems to be no proper option to speak to a person or get the issue resolved. I recently experienced one of the worst customer service experiences with Swiggy. Over time, the quality of service has been deteriorating, particularly the online customer support. What used to be a convenient platform has now become extremely frustrating to deal with.It needs to be improved.

- `REF` Customer support | negative | General | sev 2
- `AI`&nbsp; Customer support | negative | General | sev 3

**90. Differs on: themes, business line** &nbsp; (5 star)

> koi customer support nhi h month m dusri baar food kharb aaya wo bhi 750 ka worse experience koi bhi support nahi krta

- `REF` Customer support ; Food quality and packaging | negative | Food | sev 3
- `AI`&nbsp; Customer support | negative | General | sev 3
- Reference note: 5 stars despite losing 750 rupees

**91. Differs on: themes** &nbsp; (2 star)

> consistent delivery issues, as only part of orders are delivered, and if in case you miss raising ticket, their policy doesnt hv option to handle the case at later time

- `REF` Missing or undelivered order ; Refunds and cancellation | negative | General | sev 3
- `AI`&nbsp; Missing or undelivered order | negative | General | sev 3

**92. Differs on: themes** &nbsp; (2 star)

> I am really disappointed with the Swiggy. For restaurant delay, the cancellation fee is on customer and these AI bots had made it more worse. Emailed with proof that restaurant delayed my food by 15mins so cancelled order and asked for refund still no common sense for customer care...It's time a competition considering all these customer issues to launch a food delivery service if swiggy continues to think about it's bussiness instead of customers. deleting the app now alternative option is ther

- `REF` Customer support ; Refunds and cancellation | negative | Food | sev 3
- `AI`&nbsp; Refunds and cancellation | negative | Food | sev 3

**93. Differs on: severity** &nbsp; (2 star)

> very high delivery fee and extra fees

- `REF` Pricing and extra charges | negative | General | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**94. Differs on: themes** &nbsp; (2 star)

> hidden charges are very High....no 1st purchase offer.... making fool of people

- `REF` Misleading offers and pricing ; Pricing and extra charges | negative | General | sev 2
- `AI`&nbsp; Misleading offers and pricing | negative | General | sev 2

**95. Differs on: themes, business line** &nbsp; (3 star)

> yesterday experience was worse, I got an incomplete order so I didn't accept ,you charge me cancellation fee. You didn't send me right order .

- `REF` Missing or undelivered order ; Refunds and cancellation | negative | Food | sev 3
- `AI`&nbsp; Refunds and cancellation | negative | General | sev 3

**96. Differs on: severity** &nbsp; (1 star)

> Always misleading advertisements on social media.

- `REF` Misleading offers and pricing | negative | General | sev 1
- `AI`&nbsp; Misleading offers and pricing | negative | General | sev 2

**97. Differs on: severity** &nbsp; (2 star)

> too much of extra charges

- `REF` Pricing and extra charges | negative | General | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**98. Differs on: severity** &nbsp; (5 star)

> goood but prize very high🙏🙏🙏🎁🫡

- `REF` Pricing and extra charges | negative | General | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**99. Differs on: sentiment** &nbsp; (5 star)

> bit pricey but gives good discounts

- `REF` Pricing and extra charges | negative | General | sev 1
- `AI`&nbsp; Pricing and extra charges | positive | General | sev 1
- Reference note: net positive tone but names a price problem - hard call

**100. Differs on: severity** &nbsp; (4 star)

> very good application but other charges too much

- `REF` Pricing and extra charges | negative | General | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**101. Differs on: themes** &nbsp; (4 star)

> Please introduce a “Draw Your Delivery Route” feature in Swiggy. Customers should be able to draw/select their preferred safe route from the restaurant to their home, especially when the default route is unsafe, inconvenient, or blocked. The delivery partner could follow this customer-selected route. Please consider adding this safety-focused feature to make deliveries safer and more convenient for everyone. 🙏 That's why I have given 4 Stars ⭐⭐⭐⭐

- `REF` App experience and bugs | neutral | General | sev 1
- `AI`&nbsp; Other | neutral | General | sev 1
- Reference note: detailed safety feature request

**102. Differs on: severity** &nbsp; (1 star)

> the delivery charges are also very high even though ordering from nearby locations plus the tax and gst excessively high

- `REF` Pricing and extra charges | negative | General | sev 1
- `AI`&nbsp; Pricing and extra charges | negative | General | sev 2

**103. Differs on: themes, business line** &nbsp; (4 star)

> please send pepar plat

- `REF` Food quality and packaging | neutral | Food | sev 1
- `AI`&nbsp; Other | neutral | General | sev 1
- Reference note: packaging request

**104. Differs on: themes** &nbsp; (4 star)

> it's okay good but in Instamart one time I got wrong ordered items so I just asked them but their not ready to respond that it but alla good apart from this

- `REF` Customer support ; Missing or undelivered order | negative | Instamart | sev 2
- `AI`&nbsp; Missing or undelivered order | negative | Instamart | sev 2

**105. Differs on: themes, sentiment, business line** &nbsp; (3 star)

> Good for few restaurants

- `REF` Other | neutral | Food | sev 1
- `AI`&nbsp; Positive experience | positive | General | sev 1
- Reference note: ambiguous - limited restaurant choice

**106. Differs on: themes, sentiment** &nbsp; (5 star)

> time later achcha hai

- `REF` Other | neutral | General | sev 1
- `AI`&nbsp; Positive experience | positive | General | sev 1
- Reference note: ambiguous wording

**107. Differs on: themes** &nbsp; (1 star)

> Absolute shameless folks, cheats and cut throats. I have been ordering from Instamart for a long time. I order my monthly groceries from them. But their products have become a health hazard. Their Noice Namak para smells bad and tastes rotten. No resolution provided by customer care. They close the chat, no agent interaction. Lost my hard earned money. I'll complain about them to FSSAI and the Consumer Forum about their products.

- `REF` Customer support ; Food quality and packaging | negative | Instamart | sev 3
- `AI`&nbsp; Food quality and packaging | negative | Instamart | sev 3
- Reference note: food safety complaint escalated to FSSAI

**108. Differs on: themes, business line** &nbsp; (5 star)

> i ordered food from Toing app and paid rs 1831 however the order was short delivered (only 1 out of 8 items) were received. now they are not refunding my money and customer care is helpless.

- `REF` Missing or undelivered order ; Refunds and cancellation | negative | Food | sev 3
- `AI`&nbsp; Missing or undelivered order | negative | General | sev 3
- Reference note: 5 stars and describes a rival app not Swiggy

**109. Differs on: themes, business line** &nbsp; (2 star)

> Disappointed because we ordered from Macdonald but we didn't received this in order and we raised complaint, add photos, add written feedback still swiggy asked us about all this questions again.....we did not expect this from swiggy

- `REF` Customer support ; Missing or undelivered order | negative | Food | sev 3
- `AI`&nbsp; Missing or undelivered order | negative | General | sev 3

**110. Differs on: themes** &nbsp; (3 star)

> they do cheating they show different product on Instamart and deliver different damaged product and then they say no return policy

- `REF` Food quality and packaging ; Misleading offers and pricing ; Missing or undelivered order | negative | Instamart | sev 3
- `AI`&nbsp; Missing or undelivered order | negative | Instamart | sev 3

**111. Differs on: themes, severity** &nbsp; (1 star)

> The offers shown are just for the sake of doing so. I haven't received any cashback or discount from the payment method. To add on, the platform fees and delivery charges on Instamart is really high. Zepto and Blinkit are much better, have no reason to come back to this app. pathetic experience.

- `REF` Misleading offers and pricing ; Pricing and extra charges | negative | Instamart | sev 2
- `AI`&nbsp; Misleading offers and pricing | negative | Instamart | sev 3

**112. Differs on: themes, severity** &nbsp; (3 star)

> because of the delivery charges and food delivery is poor

- `REF` Delivery timing ; Pricing and extra charges | negative | Food | sev 1
- `AI`&nbsp; Delivery timing | negative | Food | sev 2
