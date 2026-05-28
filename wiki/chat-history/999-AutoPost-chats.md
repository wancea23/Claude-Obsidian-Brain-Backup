# 999-AutoPost — Chat History

> Log of important Claude Code sessions for this project.
> Paste key decisions, solutions, and context from past chats here.

---

## Format

```
### [YYYY-MM-DD] Session title
**What was asked**: brief description
**What was done**: summary of changes made
**Key decisions**: why X was chosen over Y
**Files changed**: list of modified files
**Outcome**: did it work? any follow-up needed?
```

---

## Sessions

### [2026-05-22] Skip "Cumpăra" (buyer-wanted) listings at cabinet collection

**What was asked**: Filter out every listing whose category is "Cumpăra" — they're buy-side wanted-ads, not items to repost — and never even hit the detail scraper for them.

**What was done**: Rewrote the ad-URL collection block in `main.py:cmd_scrape` from a Python-side `query_selector_all("a[href]")` loop into a single `page.evaluate(...)` JS pass that:
1. Walks every anchor whose last URL segment is a pure digit (canonical 999.md listing URL `/ro/<id>`).
2. For each match, walks up to 6 ancestors looking for a card-ish container (class includes `card`/`item`/`advert`).
3. Tests the container's `innerText` against `/\bcump[ăa]r/i` so it catches "Cumpăr", "Cumpara", "Cumpără".
4. Returns `{url, isCumpara}` per match.

Python loops the array, drops Cumpăra entries (logged as `[skip] Cumpăra listing: <url>` with a counter); the `Total ads found` line now reads `Total ads found: N (skipped K Cumpăra)`.

**Key decision**: filter at the cabinet collection stage, not after detail-scrape. User said "will not be scrapped at all" — need to drop them BEFORE the per-listing HTTP fetch. A breadcrumb-based filter inside `scrape_listing_detail` was cheaper code-wise but it would still pay the network cost.

**Why JS-evaluate + ancestor walk** instead of a CSS selector: cabinet card classes are obfuscated Next.js hashes (`styles_card__abc123`), no stable selector. Walking a few ancestors + text-content match is fine here because each card carries one ad-type label.

**Files changed**: `999 AutoPost/main.py` (ad-URL collection block in `cmd_scrape`; `Total ads found` log line).

**Outcome**: Cumpăra cards never enter `ad_urls` and never hit `scrape_listing_detail`. No DB write, no detail HTTP call. Robust to class-name churn.

---

## How to use
After finishing a session on this project, summarize it here.
Focus on: decisions made, mistakes caught, patterns that worked.

[[../projects/999-AutoPost|Back to 999-AutoPost]] · [[../index|Vault Index]]
