# 999 AutoPost — Design Decisions

> WHY things were built the way they are. Add entries as decisions are made.

---

## 2026-05-22 — Filter "Cumpăra" listings at cabinet collection, not at detail-scrape

**Decision**: The ad-URL collection block in `cmd_scrape` runs a single `page.evaluate(...)` returning `{url, isCumpara}` per listing card. Python drops `isCumpara: true` entries before they enter `ad_urls`, so they never reach `scrape_listing_detail`. Detection: walk up to 6 ancestors from the listing anchor to a card-ish container (`card`/`item`/`advert` in className), test `innerText` against `/\bcump[ăa]r/i` (matches Cumpăr, Cumpara, Cumpără).

**Why**: Cumpăra listings are buyer wanted-ads, not items the user posts for sale — they must never be reposted. Filtering at the detail-scrape stage (e.g. via breadcrumb) was simpler code-wise but still paid the network cost per listing. User said "will not be scrapped at all" — needed to drop them BEFORE the per-listing HTTP fetch.

**How to apply**: any "filter out X type of source item" requirement should be enforced as early in the pipeline as possible. Cabinet-page filtering > detail-page filtering > post-fetch filtering > DB-level filtering. Use `page.evaluate` for DOM walking + text-content checks when CSS selectors are unreliable (obfuscated Next.js class hashes here — `styles_card__<hash>`).

---

[[../projects/999-AutoPost|← Back to 999 AutoPost wiki]] · [[../decisions|← Global Decisions]]
