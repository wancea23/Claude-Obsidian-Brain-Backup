# 999 CarScrapper — Web UI Performance (slow page load fix)

> The web UI felt slow: the main grid took ~600 ms, opening a listing ~800 ms,
> and the filter dropdowns / KPIs spun for ~10 s on a cold cache. Root cause was
> three separate things — a query that re-scanned a whole history table every
> request, missing indexes that forced full table SCANs, and a front-end that
> loaded the car grid LAST. This page is the canonical reference for what was
> slow, why, and the indexes that must exist for the web UI to stay fast.

Related: [[projects/999-CarScrapper]] · [[999-CarScrapper-dedup-consistency]] · [[decisions/999-CarScrapper-decisions]]

Date: 2026-06-05 · DB at the time: `E:\DB\listings.db` ≈ 1.6 GB, ~88 k listings, 153 k price-history rows.

---

## Results (measured over HTTP, steady-state)

| Surface | Endpoint | Before | After |
|---|---|---:|---:|
| Main car grid | `/api/listings` | 592 ms | **15 ms** |
| Open a listing | `/api/listings/{id}` | 810 ms | **10 ms** |
| Filter dropdowns | `/api/facets` | 9.6 s | **13 ms** (1 ms cached) |
| KPIs / dashboard | `/api/stats` | 10.5 s | **14 ms** (1 ms cached) |
| Sort by price | `/api/listings?sort=price` | 661 ms | **11 ms** |

Plus the grid now **paints first** instead of behind facets + stats.

---

## The 4 root causes & fixes

### 1. Main query re-materialised the whole price-history table every request
`web/queries.py:build_listing_query` joined a `ph_agg` derived table that did
`GROUP BY listing_id` over **all 153 k** `price_history` rows to build a
per-listing price summary — then threw away all but the 24 shown. SQLite
`MATERIALIZE`d it on every request (~600 ms).

**Fix**: paginate FIRST, decorate SECOND. The 24 listings for the page are
selected (WHERE + ORDER BY + LIMIT/OFFSET) in a `WITH page AS (...)` CTE, then
thumbnail / prediction / price-summary are attached to only those 24 survivors
via correlated subqueries (`price_history` is indexed on `listing_id`). 592 ms → 1 ms at the SQL layer. Output columns unchanged (34 cols, verified identical shape across default / filtered / sorted / removed / search / deep-page).

### 2. Opening a listing did full table SCANs
`mileage_history` and `description_history` had **no index on `listing_id`**.
`description_history` alone = **760 ms** per listing open.

**Fix**: `idx_mileage_history_listing` + `idx_description_history_listing` on
`(listing_id, recorded_at)`. → 0.1–22 ms.

### 3. Facets/stats fetched fat rows just to apply the buyer-side filter
`/api/facets` GROUP BYs filter on `status=? AND (offer_type IS NULL OR offer_type
!= 'Cumpăr')`. The old `(status, <col>)` indexes did **not** contain `offer_type`,
so `COUNT()` fetched every active row — including the fat `description`/`raw_html`
columns — just to test the buyer filter. ~700 ms/column × 8 + ranges ≈ 9.6 s.

**Fix**: covering indexes with `offer_type` as a trailing column (see table
below). Each GROUP BY becomes a COVERING scan that never touches the row. → ~12 ms each.

### 4. The grid loaded LAST (front-end)
`web/static/app.js` `init()` was fully sequential:
`loadMarks → loadFacets → renderKpis (awaits /api/stats) → fetchListings`.
So the main content waited ~10 s behind analytics.

**Fix**: fetch the grid immediately; `loadFacets()` and `renderKpis()` run
in parallel / fire-and-forget around it. `loadMarks()` still awaited first (tiny
file read, needed for mark badges).

---

## Required web-UI indexes (the golden list)

All live in the DB **and** persisted in `db/schema.sql` + `scripts/add_web_indexes.py`
(`python -m scripts.add_web_indexes`, re-run-safe). If a query regresses, check these exist + `ANALYZE` ran.

| Index | Columns | Serves |
|---|---|---|
| `idx_mileage_history_listing` | `(listing_id, recorded_at)` | listing detail mileage timeline |
| `idx_description_history_listing` | `(listing_id, recorded_at)` | listing detail desc timeline (was the 760 ms killer) |
| `idx_listings_status_price_sort` | `(status, COALESCE(price_eur, price_usd, price_mdl/19.0))` | sort-by-price (expression index matching `ALLOWED_SORTS['price']`) |
| `idx_fc_make` / `_engine_type` / `_transmission` / `_drive` / `_body_type` / `_color` / `_location` / `_seller_type` | `(status, <col>, offer_type)` | each `/api/facets` GROUP BY — COVERING |
| `idx_fc_ranges` | `(status, offer_type, year, price_eur, price_mdl, mileage_km, engine_l)` | facets MIN/MAX range block |
| `idx_fc_make_price` | `(status, make, offer_type, price_eur)` | `/api/stats` avg-price-by-make — keeps it COVERING |

---

## Gotchas / notes

- **`offer_type` MUST be trailing in the facet indexes.** The buyer-side filter
  `(offer_type IS NULL OR offer_type != 'Cumpăr')` is an OR predicate — a *partial*
  index with that WHERE clause is NOT matched by the planner (tested; it fell back
  to the non-covering index). Putting `offer_type` as an indexed column instead
  makes the scan covering and works.
- **Cold-start ~2 s is the ML trainer, not the queries.** `web/ml.py`
  `start_background_trainer()` runs sklearn training on boot and contends for
  CPU/disk for the first few seconds after a server restart. Steady-state is all
  sub-20 ms. Candidate follow-up: defer the first train a few seconds after boot.
- **`/api/stats` still has a 447 ms `price_drops` CTE** (full GROUP BY MIN/MAX over
  all `price_history`). Left as-is: it's behind the 60 s TTL cache and no longer
  blocks the UI. Optimise only if it surfaces.
- Read-only / WAL-safe: no scraper or write-path changes, indexes built live
  alongside the running scraper.
- **To deploy the front-end + query changes: restart uvicorn.** The DB indexes
  are already active; the restart picks up `queries.py` + `app.js`.
