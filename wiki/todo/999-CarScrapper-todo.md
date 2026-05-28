# 999 CarScrapper — Todo & Known Issues

---

## High Priority
- ~~**Retro-cluster the legacy 96k unclustered listings**~~ — **DONE 2026-05-24**. 99,458/99,458 clustered; chimeras dropped 78 → 2 (97% reduction); 12,893 multi-member relists detected. Algorithm now uses template-phash filter (span ≥2 distinct make+model) + make+model gate + defensive `assign_cluster` guard. Run `python -m scripts.dissolve_chimeras --apply` to clean up the 2 leftover true cross-make clusters (Volvo+Opel, Skoda+Opel). **Restart any long-running `scheduler.py` daemon** after pulling these changes so it picks up the patched `db.database` (Python doesn't auto-reload imports).
- **Self-heal cluster gap on refresh path** — extend `pipeline.py:_scrape_one` to also call `find_cluster_for_photos` + `assign_cluster` when `car_identity_id IS NULL` on the refresh branch (currently only the `is_new=True` branch does it). Prevents the 97% backlog from recurring if clustering logic is ever re-introduced after data exists.
- **Fix `seller_id` parser** — currently NULL for ~98% of rows (1/90 Corolla candidates had it). Re-extract from 999.md detail page (profile link → seller slug). Unlocks "seller + specs" duplicate fingerprint as a complement to pHash for sellers who re-photograph the same car.
- **Deploy public site** — see [[../decisions/999-CarScrapper-decisions|decision 2026-05-22]]. Plan: Cloudflare R2 for ~149 GB photos (zero egress, ~$2.25/mo), Litestream-replicated SQLite, Hetzner CPX11 (€4/mo) running `web/app.py` read-only. Steps: (1) provision R2 bucket + token, (2) `rclone sync E:\DB\photos r2:bucket`, (3) wire `scraper/photo.py` to upload each new webp inline, (4) install Litestream locally + on VPS, (5) deploy Caddy + uvicorn, (6) flip frontend `<img src>` to R2 URLs.
- **Push archived listing count past 500** — current ~559+. Should already trigger automatic retraining on next daemon tick. Verify Analysis tab shows trained state (not "collecting data") after next refresh.
- **Smart-refresh via auth** — introspection (2026-05-19 late) confirmed `Advert.reseted/posted/expire` exist but return empty strings for anonymous callers; `getAdsByIds` returns `UNAUTHENTICATED`. The 3h → 15min refresh win requires either a 999.md account + cookie injection in the Session, or a weaker fallback (title-diff against GraphQL summary). For now, use `--refresh-older-than 24` for incremental nightly runs.
- **Adopt `--refresh-older-than` as the daily pattern** — full `--refresh-known` is now ~4.5h. The incremental flag runs nightly in ~15 min once steady state. Add to `scheduler.py` once verified.

## Improvements
- **Price alerts** — notify (email/Telegram) when a car matching saved filters drops in price or a new listing appears. Scraper schedule provides the trigger; needs a notification backend.
- **Saved searches** — persist filter combos (e.g. "BMW 3 Series, 2018+, <15k€, diesel") server-side. Show a count badge when new matches appear since last visit.
- **Comparison mode** — select 2-3 cards and see specs side by side (price, mileage, age, predicted fair price).
- **`view_count` / `views_today`** — JS-injected, requires a separate `AdViews` GraphQL call per listing. Useful as a "hot listing" feature for the ML model. Deferred during the analytics build.
- **XGBoost upgrade** — currently optional. `pip install xgboost` and the trainer auto-switches; expect ~10-20% MAE improvement on fair-price.
- **`lifelines` for days-to-sell** — current Ridge predictor gets R²<0 because all 407 archived listings share `removed_at=today`. Switch to Cox PH survival once we have multi-week lifecycle data; auto-detected at import.
- **Smart-refresh** (see High Priority).
- **Map view** — `location` is just a city string ("Chișinău mun.", "Bălți"). Geocode once (Nominatim) into a `locations` table with lat/lon, then add a Leaflet/MapLibre map tab to the UI.
- ~~**Perceptual photo hash (pHash)** — detect when a "new" listing is the same car relisted with a new ID.~~ **Done 2026-05-22** (see Completed). Future follow-ups under pHash: tune Hamming threshold from live data (currently 6); add a Dashboard "Top relisters" tile showing dealers with the most cluster matches; backfill phase 1 takes a while on 1.14 M photos — consider parallelising file reads.
- **Phone-number capture** — the "Arată numărul" button on 999.md reveals the seller phone via API. Same phone across many listings = dealer cluster signal.
- **VIN decoding** — when `vin` field is populated, hit a free vindecoder API (NHTSA) to enrich body/engine/factory data.
- **Daily NBM EUR/MDL rate** — fetch once a day from `https://www.bnm.md/...`, fill missing currency at scrape-time so historical prices are comparable.
- **CSV export endpoint** — `/api/listings.csv?<filters>` streaming response, reuses queries.py.
- **Compare 2–3 listings side-by-side** — checkbox on cards → comparison bar → side-by-side spec view.
- **Predict-on-insert hook** — currently `price_predictions` is filled in a batch every 24h; new listings between retrains don't get flagged immediately. Could add a lightweight per-row predict at `insert_listing` time. Acceptable staleness for now — revisit if visible.

## Known Issues
- **Orphaned `scrape_runs.status='running'`** — if `pipeline.py` is killed (Ctrl+C, OS kill, terminal close), the finish_run UPDATE never fires. Cosmetic only; no data corruption. Fix: a startup sweep that marks any pre-existing 'running' rows as 'failed'.
- **Two concurrent pipeline processes contend for the SQLite file** — the second one will mostly succeed via WAL but writes can lock briefly. Add a PID/lock file check at pipeline start.
- ~~**Long-running scraper holds 10+ GB of RAM by end of crawl**~~ — **fixed 2026-05-19**: chunked processing with per-chunk Session recycle + `gc.collect()` keeps RSS flat at a few hundred MB.
- **Detail view shows raw value for `steering` ("Stânga"/"Dreapta") and `drive` ("4x4"/"Față")** — these are Romanian as scraped. Fine, but maybe a small i18n map for the UI would polish it.
- **Some listings show no thumbnail** — listings inserted by killed scrapes have rows in `listings` but no rows in `photos`. Self-corrects on `--refresh-known`.
- **`power_hp` is only ~30% populated** — many sellers omit it. Not a parser bug; genuine data sparsity.

## Completed ✓ (2026-05-27 session — Sell-through tab, cluster dedup fix, model_stats fix)
- [x] **Sell-through tab** — new 5th tab showing ranked (make, model, year_bucket, fuel, mileage_bucket) combos by sell-through %. Year buckets: 5-year windows (2014-2018, 2019-2023, 2024+). Mileage: 0-100k / 100k+. Top 40 makes only. Time-window toggle (30/60/90/180d). Client-side year-chip filter. Sortable columns. Backend: `sell_through_segments()` in `analytics.py` + `/api/analytics/sell_through_segments` endpoint.
- [x] **Refactored dedup SQL** — extracted `_cluster_dedup_sql(pfx)` and `_dedup_sql(pfx)` as module-level helpers in `analytics.py`. Fixed ambiguous column name bug (unqualified names inside NOT EXISTS resolved to inner scope). `model_stats()` now uses the shared helpers instead of inline SQL.
- [x] **Fixed model_stats sold counts** — `sold_total_truly` / `sold_recent_truly` now apply both relisting filter AND cluster dedup (previously only relisting). Numbers now match the Browse grid exactly (e.g., Honda CR-V Plug-in Hybrid 2019+: 4 sold in both views).
- [x] **Fixed model_stats sold-related stats** — `avg_days_to_sell`, `avg_price_sold`, `sold_by_year` all apply the same full dedup, so every metric in the side-card is consistent with the grid.
- [x] **Updated info tooltips** — "X relistings excluded" → "X duplicate/relisted listings excluded" to reflect both dedup types.
- [x] **Fixed `database is locked` crash** — `db/database.py:connect()` and `init_db()` had no `timeout` param. `sqlite3.connect(timeout=30)` makes SQLite retry for 30s on lock contention instead of failing instantly. Root cause: web server (read-only WAL) can briefly block writers during checkpoint.

## Completed ✓ (2026-05-26 session — KPI auto-refresh, hide-ordered filter, dealer query)
- [x] **KPI auto-refresh with slide animation** — `renderKpis()` polls every 30s, tracks previous values in `_kpiPrev`, animates only changed tiles with a 450ms `translateY(100%→0)` CSS slide-up. First paint is instant.
- [x] **"Hide ordered" filter** — new checkbox in Browse toolbar, excludes `availability = 'La comandă'` and `offer_type = 'Auto la comandă'`. Wired through `web/queries.py` (grid) and `web/analytics.py:build_extra_filters` (model-stats card). URL-synced via `?hideOrdered=1`. No description parsing.
- [x] **Dealer count query** — investigated dealer listings with 100+ cars. Result: 0 dealers cross the threshold (AGMOTORS leads at 90). `seller_id` is NULL for ~98% of rows, limiting dealer analysis.

## Completed ✓ (2026-05-25 session — sold dates, marks, sort fix)
- [x] **Sold date on listing cards** — bottom row now shows `sold dd/mm/yyyy · Xd listed` for removed/sold listings. New `fmtSoldDate()` helper, no backend change.
- [x] **Mark/bookmark feature with gold contour** — ★ button on each card (top-left corner), gold `2px solid #d4af37` border + glow on marked cards. Server-side persistence via `marks.json` + 3 API endpoints (`GET/POST/DELETE /api/marks/{id}`). Loaded at app init; works across devices.
- [x] **"Recently sold" sort option** — new `sold_at` sort key (`COALESCE(removed_at, sold_at, last_seen_at)`). Removed tab auto-selects it; Active tab reverts to "Newest first".

## Completed ✓ (2026-05-22 session — pHash + Removed pagination + model analytics + cohort restyle)
- [x] **pHash relisted-car clusters** — `photos.phash` (signed 64-bit), `car_identity` table (`id, first_seen_at, last_seen_at, listing_count, current_listing_id, status, removed_at`), `listings.car_identity_id` + `relisted_from_listing_id`. `find_cluster_for_photos` matches first 3 photo phashes (Hamming ≤ 6, ≥ 2 must match) against existing photos. `assign_cluster` joins or creates singleton; new listing becomes cluster head. `reconcile_cluster_status` flips cluster → 'removed' only when no member is still active. `scripts/backfill_phash.py --phase all` hashes existing webp files then clusters historically.
- [x] **Relisted UI** — `/api/listings/{id}` returns `cluster: {members, listing_count, first_seen_at, last_seen_at}`. Detail modal shows "🔁 Relisted Nx — same car first seen YYYY-MM-DD, K days on market" badge with clickable twin chips.
- [x] **Cluster-aware soft-archive** — `verify_sold.delete_listing` and `mark_sold` both call `reconcile_cluster_status` so cluster stays alive while ANY member is active.
- [x] **Removed tab pagination fix** — `web/queries.py` flips `has_user_filters = True` when status is `sold`/`removed`/`all`, so `/api/listings` runs a real `COUNT(*)` instead of reusing the cached 89k active count. Removed tab now paginates the ~6,861 rows correctly.
- [x] **Status-scoped facets** — `/api/facets` and `/api/models` accept `status=`. Cache keys include status. Frontend forwards `state.filters.status` and the status toggle re-runs `loadFacets()` before refetching (preserving prior make/model if still valid).
- [x] **Model-cohort analytics endpoint** — `web/analytics.py:model_stats(make, model, recent_days, filters)` returning active, sold_total, sold_recent, median_sold_eur, avg_price_active_eur, avg_days_to_sell, `sold_by_year` (year + count, no zero-rows), and `filters_applied` flag. `/api/analytics/model_stats` accepts the full sidebar filter set.
- [x] **Popularity tile** — `web/analytics.py:popularity(days, limit)` returning ranked `(make, model)` by sold + listed + active + velocity %. Rendered as a Dashboard table.
- [x] **`build_extra_filters(params, alias)` helper** — shared WHERE-builder used by `model_stats` (matches `web/queries.py` parsing), accepts alias prefix so JOIN queries (median-price subquery) can reuse the same args without string-replacing column names.
- [x] **Cohort card filter-aware** — every stat respects sidebar filters (year/price/mileage/engine ranges, fuel/transmission/drive/body/color, seller_type, location, q). Endpoint strips listing-only params (`page`/`page_size`/`sort`/`sort_dir`/`status`/`dealsOnly`) so they don't bust the cache.
- [x] **Cohort card restyle** (ui-ux-pro-max) — rebuilt against the real `--surface`/`--surface-2`/`--surface-3`/`--border`/`--accent-soft`/`--accent-border` tokens (previous version's `--card`/`--divider`/`--bg-elevated` were undefined → chips dissolved into a run-on string). Single composed surface with internal hairline dividers between 6 stat tiles. Pill chips for window + "matching filters" tag. Year chips render as `<b>year</b><i>count</i>` for instant pair-grouping. tabular-nums + tight letter-spacing on values. Grid collapses 6 → 3 → 2 columns at 1100/600 px.
- [x] **Migration order fix** — `db.init_db()` now runs `ALTER TABLE` migrations BEFORE `executescript(schema.sql)`. schema.sql contains `CREATE INDEX idx_photos_phash` which referenced a column missing from existing DBs and aborted the whole script.
- [x] **pHash u64 → signed 64-bit wrap** — `imagehash.phash` returns unsigned 64-bit; SQLite INTEGER is signed (`OverflowError`). Both live encoder and backfill wrap `if u >= 2**63: u -= 2**64`. XOR-based Hamming is bit-identical so comparison unaffected.

## Completed ✓ (2026-05-21 web session)
- [x] **USD on the web layer** — `web/queries.py` SELECTs `price_usd`, sorts `COALESCE(eur, usd, mdl/19)`, accepts `currency=USD` filter; `web/app.py` price_history endpoint returns `price_usd`; `app.js` `fmtPrice(eur, mdl, usd, cur)` displays `$37,850` with 3-arg back-compat shim. 2,106 active USD listings now visible
- [x] **Period field in modal** — `_ddmmyyyy()` + `fmtPeriod(it)` helpers; renders `dd/mm/yyyy - current` for active and `dd/mm/yyyy - dd/mm/yyyy` for sold/removed
- [x] **Period in top-right header** — `.detail-price-row` wrapper with `justify-content: space-between` puts price left, period badge right; price block uses `align-items: stretch` + `min-width: 320px`
- [x] **Cache-bust pipeline** — `index()` injects `?v=<mtime>` into asset URLs + sends HTML `Cache-Control: no-cache`; `NoCacheStaticFiles` subclass sends `no-cache` on every JS/CSS response. Three independent layers
- [x] **Portrait photos fit in modal** — `.detail-photos .main-photo` rewritten as `display: flex` + img `max-w/h: 100% width/height: auto` (was grid+100% dimensions, hit circular sizing dep that overflowed 9:16 photos to 1414px tall)

## Completed ✓ (2026-05-21 session)
- [x] **USD currency capture** — added `price_usd`, `old_price_usd` to `listings`, `price_usd` to `price_history`; parser regex now matches `$|USD`; `_parse_prices()` returns a 4-tuple; `init_db()` runs additive `ALTER TABLE` migrations for existing DBs
- [x] **Mid-run deletion detection** — refresh worker treats parse-stub (no make + no price in any currency) as deleted listing → soft-archive via `delete_listing`, never overwrites real data with NULLs. Stat key: `listings_removed`. Logged as `DEL <id> (deleted mid-run)`
- [x] **Killed the `?` log noise** — `[N/M] upd <id> ? ?y ?€` was the symptom of the silent NULL-overwrite bug. Worker log now prints only fields that exist; price shows in whichever currency is set (`€` / `$` / `MDL`)
- [x] **`fast=True` is the default** in `pipeline.run()`; CLI exposes `--no-fast` opt-out. Closes the gap where `python pipeline.py --mode full` was 4-5× slower than the scheduler's tick/incr jobs
- [x] **`tick` mode runs verify-missing** — `if mode in ("full", "tick"):` in pipeline. Deleted listings archived within 10 min instead of waiting for the Sunday `full`. Safety guard (50% discovery floor) preserved

## Completed ✓ (2026-05-19 late session)
- [x] **Analytics SQL rewrite** — kpis 9.5s → 477ms, sell_through 9.3s → 700ms (single-pass GROUP BY vs O(N²) correlated subquery). Ran `ANALYZE` on live DB.
- [x] **Junk-data filter in ML** — `year IS NOT NULL AND year BETWEEN 1980-2030 AND mileage_km BETWEEN 1000-500000 AND price_eur BETWEEN 500-200000` at both training AND prediction-cache fill. Plus delta clamps (`-90 < delta < 500`).
- [x] **Dashboard layout collapse** — `body[data-tab]` CSS + `.filters{grid-column:1}; .results{grid-column:2}` so non-Browse tabs use full width
- [x] **Chart.js infinite-grow fix** — `.chart-box { position:relative; height:240px }` wrapper around every canvas
- [x] **Analysis tab UI rewrite** — single combined predictor with live debounced updates, verdict tile (DEAL/A BIT LOW/FAIR/A BIT HIGH/PRICEY), grouped form (CAR/TECH/SPEC/CONTEXT), filterable hot-deals feed (max € + make), explainer card, dropped the useless scatter
- [x] **Speed: `--fast` actually applies** — Session reads config at construction, not as default arg
- [x] **Speed: removed global `sem_lock`** — 16 workers truly parallel; throughput 2.7 → 5.4 listings/s
- [x] **Speed: fast-path in update_listing** — skip 40-col UPDATE + feature sync when nothing changed
- [x] **Speed: HTTP/2 → HTTP/1.1 on CDN** — killed StreamReset errors from photo fetches
- [x] **Speed: `--fast` recalibrated** — sem=12 (was 16/24), delay (50,150) based on direct benchmark of 999.md throttle
- [x] **`--shard N/M`** — parallel scraping with manifest-based discovery sharing; documented "doesn't help because of per-IP throttle"
- [x] **`--refresh-older-than HOURS`** — incremental refresh by `last_fetched_at` age
- [x] **`scripts/run_parallel.ps1`** — PowerShell helper for parallel runs (Get-Process kill stale; Start-Process N shards; background mode with log redirection)
- [x] **Dropped misleading `listings_deleted` stat key** — the count was correct semantically (soft-archive) but the word triggered user PTSD from the 235-row catastrophe

## Completed ✓ (2026-05-19 earlier session)
- [x] **STOP destructive deletion** — `verify_sold.delete_listing` rewrote to soft-archive (`status='removed'`, `removed_at=now`, photos kept)
- [x] **DB hot-backup** — `scripts/backup_db.py` + auto-runs before every `--mode full` (keeps last 14 in `E:\DB\backups\`)
- [x] **Recovery attempt** — `scripts/recover_orphans.py` (9 orphan folders found, all empty + 999.md "not found" → unrecoverable)
- [x] **Web UI perf** — `scripts/add_web_indexes.py` (8 composite/expression indexes), 60s TTLCache on `/api/facets`/`stats`/`makes`/`models`/unfiltered-count, LEFT JOIN for thumbs
- [x] **Catch-all field history** — `listing_field_history` table + diff in `update_listing` over 33 scalar fields
- [x] **Photo history** — `photo_history` table + diff in `insert_photos` (added/removed/replaced events)
- [x] **Status transition logging** — `touch_seen`, `mark_sold`, soft-archive all write to field history
- [x] **Optional features extraction** — `FEATURES_CATALOG` (49 entries: Securitate + Confort) + Unicode normalisation + `listing_features` + `feature_history` tables
- [x] **Scraper fields**: `site_updated_at`, `offer_type` (dropped `view_count`/`is_negotiable`/`views_today` — JS-injected or non-existent)
- [x] **`lxml` parser** + `asyncio.to_thread` around `parse_listing` (~3-5× faster: 150 ms → 40 ms per listing)
- [x] **Analytics endpoints** — `web/analytics.py` with 7 endpoints (KPIs, days-to-sell-by-make, drop effectiveness, value retention, sell-through heatmap, DOW trends, stuck inventory) — outlier-filtered, 60s cache
- [x] **ML pipeline** — `web/ml.py` with Ridge + OneHotEncoder, 24h daemon retrain, pickle warm-start, 500-row gate, predictions clamped to [€500, €500k]
- [x] **`price_predictions` cache table** + `/api/listings` JOIN + `dealsOnly` filter
- [x] **Frontend**: Chart.js 4.4 CDN, new Analysis tab (status gate / predictor forms / hot deals / scatter), Dashboard extended (5 mini-KPIs + 8 new cards), Browse "Deals only" toggle + DEAL/PRICEY badges, Favorites refresh (header stats + grid/list toggle + sort)
- [x] **README rewrite** for the new 4-tab UI + Analytics & ML section + dealsOnly filter + Captured fields update

## Completed ✓ (earlier 2026-05 sessions)
- [x] Scraper end-to-end (discover → diff → scrape → mark sold) — 2026-05-18
- [x] WebP photo pipeline at 1280×960, q=82, method=2
- [x] DB schema with 6 tables (listings, photos, 3 history, scrape_runs), WAL, indexes
- [x] Async HTTP client with per-host semaphores + UA rotation + 429 backoff
- [x] Speed optimization: 8.5 min → 70 s for a 2-page test (7.2× faster)
- [x] FastAPI web app: 6 endpoints, read-only SQLite, static photo serving
- [x] Single-page vanilla JS UI: grid + table, filters, sort, pagination, detail modal, dashboard, favorites
- [x] Romanian-aware `_normalize_seller_type` (matches "persoan", not just "person")
- [x] Storage moved to `E:\DB\` (off OneDrive sync)
- [x] Strip script/style tags before text extraction (defence against i18n-leak bug class)
- [x] `[hidden] { display: none !important }` guard — fixes modal overlay blocking clicks — 2026-05-19
- [x] `scripts/verify_sold.py` — reconcile sold rows with reality (delete genuinely-gone, revert false positives) — 2026-05-19
- [x] Pipeline verifies each missing-from-discovery listing before flagging it sold — 2026-05-19
- [x] 50%-discovery safety guard in pipeline (skip sold-marking if crawl looks partial) — 2026-05-19
- [x] UI relabel "Sold" → "Removed" + amber detail-view banner explaining the state — 2026-05-19
- [x] Price-parser fix: specific selectors (`price__main` + `oldprice__value`) instead of wrapper — 2026-05-19
- [x] Added `old_price_eur` / `old_price_mdl` columns via live `ALTER TABLE` — 2026-05-19
- [x] Chunked scrape with per-batch Session recycle + `gc.collect()` (`SCRAPE_CHUNK_SIZE = 500`) — bounds RSS — 2026-05-19
- [x] Optional `psutil` for in-log RSS readout per chunk — 2026-05-19
- [x] `scripts/__init__.py` for cross-version package import safety — 2026-05-19
- [x] README rewrite covering GraphQL discovery, verify-sold, chunk-recycle, all config knobs, gotchas — 2026-05-19
- [x] Cluster-aware Removed tab: `NOT EXISTS active sibling` in `web/queries.py` so relisted cars don't appear under Sold — 2026-05-23
- [x] Merged cluster price + mileage history in `get_listing()` — points tagged with `listing_id`, chart colors siblings dimmer — 2026-05-23
- [x] Truly-sold counts in `analytics.model_stats` (`sold_recent_truly` / `sold_total_truly` + `relisted_recent` / `relisted_total`) — 2026-05-23
- [x] Unique-car Active count + duplicates info-tooltip in model-stats card (`COUNT(DISTINCT COALESCE(car_identity_id, -id))`) — 2026-05-23
- [x] Plug `_NOT_BUYER` into `web/analytics.py` (top-bar KPI vs model-stats card now match) — 2026-05-23
- [x] Detail-modal price/mileage history → Chart.js time-series with visible points (`chartjs-adapter-date-fns`) — 2026-05-23
- [x] Themed scrollbars via `var(--border-strong)` + slim 8px variant for modal/filter/thumb-strip — 2026-05-23
- [x] Sell-through tile in model-stats card (`truly_sold / (active + truly_sold)`) with tiered display + info tooltip — 2026-05-23

## Next on the cluster-aware path
- [ ] **Daily NBM EUR/MDL + USD/MDL rate ingest** — per the user's note, the merged price history mixes currencies (EUR / MDL / USD) and the chart must keep the ORIGINAL currency each point was spotted in. Need a `fx_rates` table keyed by `date` with `eur_mdl` + `usd_mdl` columns, populated nightly from NBM (`https://www.bnm.md/`). At chart time, convert each point's native currency → display currency using the rate from that point's `recorded_at` date. Don't store converted values — store native + look up rate at render time. Affects: scraper (capture original currency per `price_history` row — already in schema), backend (`get_listing` resolver), frontend (chart Y-axis formatter).
- [ ] **Sanity-check that `analytics.popularity`, `analytics.value_retention`, `analytics.days_to_sell_by_make` and the rest still pass `_NOT_BUYER`** — only `model_stats` was audited in this pass. Grep `web/analytics.py` for `FROM listings` and verify every query has either `_NOT_BUYER` AND'd in or goes through `REMOVED_FILTER` (which now carries it).
- [ ] **Move `_NOT_BUYER` constant duplication to a shared module** — currently defined in both `web/app.py` and `web/analytics.py`. Both copies are identical; if one drifts the symptom is silent inflation of one set of endpoints. Candidate home: `web/queries.py` (it's already the SQL-fragment file) — both modules already import from it.

[[../projects/999-CarScrapper|← Back to 999 CarScrapper wiki]]
