# 999 AutoPost — Todo & Known Issues

---

## High Priority
*(none)*

## Improvements
*(none)*

## Known Issues
*(none)*

## Completed ✓
- [x] **Skip "Cumpăra" listings at cabinet collection** (2026-05-22) — `cmd_scrape` ad-URL loop rewritten as a single `page.evaluate` returning `{url, isCumpara}`. Walks up to 6 ancestors to a card container, tests `innerText` against `/\bcump[ăa]r/i`. Buyer-wanted ads dropped before they reach `scrape_listing_detail` (no DB write, no detail HTTP call). `Total ads found` log line now includes `(skipped K Cumpăra)`.

[[../projects/999-AutoPost|← Back to 999 AutoPost wiki]]
