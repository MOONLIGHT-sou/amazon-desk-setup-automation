# Product Selection Policy

This policy governs which Amazon Desk Setup products enter the automation queue. It is a selection policy, not a production-content claim source.

## Priority order

1. **Exact product identity and variant** — verify the exact Amazon listing/variant first.
2. **Purchase signal** — when Amazon explicitly shows a reliable purchase signal (for example, a recent purchase-volume badge), treat it as the strongest demand signal. Never invent or estimate a purchase count.
3. **Review volume** — prefer products with substantial review volume over products with very few reviews. Review count is evidence of observed buyer activity, not proof of product quality.
4. **Rating** — use rating as a quality signal, but never use star rating alone. A 4.8 rating from 20 reviews is weaker evidence than a 4.6 rating from hundreds of reviews.
5. **Review quality/themes** — manually inspect recurring complaints, failure modes, compatibility problems, and seller/variant confusion before selection.
6. **Niche fit** — the product must solve a real desk-setup problem and fit the Minimal Desk Setup content strategy.
7. **Content safety** — only select products whose current listing facts can be verified well enough to support conservative, non-fabricated content.

## Selection rule

A product should not be promoted merely because it has a high star rating. Strong candidates combine **real demand evidence + meaningful review volume + solid rating + clear niche fit + verifiable product facts**.

When purchase-volume information is unavailable, record it as **unknown**. Do not infer demand from price, search position, sponsored placement, or appearance.

## P004 record

P004 is currently the verified example: the Amazon listing screenshot showed a **4.6 rating and 211 ratings/reviews** for the displayed Quntis Monitor Light Bar Focus variant. These figures are evidence captured at verification time, not permanent current values. The current price shown in the screenshot is deliberately not frozen as a content fact because Amazon prices change.

## Before adding the next product

Capture and review, at minimum:

- Exact product/variant name
- Current Amazon URL
- Purchase-volume signal, if explicitly shown
- Current star rating
- Current review count
- Important recurring review complaints
- Key product facts that are safe to state
- Facts that must not be claimed without re-checking
- Verification date

The automation must remain conservative: missing evidence is **unknown**, not permission to guess.
