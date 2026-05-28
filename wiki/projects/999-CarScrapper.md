# 999 CarScrapper

> Async Python scraper for 999.md car listings → SQLite + WebP photos + FastAPI web UI with ML-powered analytics · full append-only audit trail (price/mileage/desc/title/status/photos/features) · soft-archive on removal · fair-price + days-to-sell predictors · pHash relisted-car clustering
> **Last synced**: 2026-05-26

**Current data size**: `listings.db` ≈ 1 GB · `photos\` ≈ 149 GB (1.14 M webp across ~88 k listings). Deployment plan is to split — see [[#Deployment Plan]].

**Path**: `Code/999 CarScrapper/`
**Stack**: Python (httpx async, BeautifulSoup, Pillow, FastAPI, uvicorn), SQLite, vanilla JS/HTML/CSS
**Storage**: `E:\DB\` (DB + photos, 1 TB drive)
**Sister project**: [[999-AutoPost|999 AutoPost]] (also targets 999.md but for reposting)

---

## What It Does

### User Experience
- One-command full sweep of every car listing on 999.md (~88,000 cars)
- Open the web UI at `http://localhost:8000` to browse, filter, sort
- Search by make/model, year/price/mileage ranges, fuel/transmission/drive/body/color
- Click any card → full spec sheet + photo gallery + price/mileage history sparkline
- Dashboard tab: top makes, avg price per make, fuel distribution, recent price drops, sold-this-week
- Dark/light/auto theme, favorites (localStorage), URL-state sync (shareable filter links)
- Continuous mode: scheduler runs full sweep every 6 h + quick top-pages check every 45 min

### System Experience
- `pipeline.py` — orchestrator: DISCOVER (GraphQL) → DIFF (set math) → FULL SCRAPE (new only) → MARK SOLD
- `scheduler.py` — cron loop (full / quick / refresh-known)
- `scraper/crawler.py` — POSTs to `https://999.md/graphql` (op `SearchAds`, subCategoryId 659) for fast ID discovery
- `scraper/parser.py` — SSR-side HTML parse on `https://999.md/ro/<id>` (full spec list, photos, description, location)
- `scraper/photo.py` — parallel photo fetch per listing, Pillow encode in worker thread → WebP
- `scraper/session.py` — async httpx with split semaphores (site polite, CDN aggressive)
- `db/database.py` — SQLite ops with append-only history tables (price/mileage/description)
- `web/app.py` — FastAPI (read-only SQLite, can run alongside scraper)
- `web/static/*` — vanilla-JS single-page UI, no framework

---

## Key Files
| File | Role |
|------|------|
| `config.py` | Tunables: concurrency, delays, paths (env var `DATA_DIR` overrides) |
| `pipeline.py` | One scrape run (full / quick / refresh-known) |
| `scheduler.py` | Continuous background cron |
| `scheduler_f.py` | Production scheduler (locked to tick-only: discovery + new-listings every 10 min) |
| `refresher_loop.py` | Sister process — loops `--mode full --refresh-known` continuously |
| `scraper/crawler.py` | GraphQL listing-ID discovery |
| `scraper/parser.py` | BeautifulSoup field extractor for SSR detail pages |
| `scraper/photo.py` | Parallel image download + WebP encode |
| `scraper/session.py` | Per-host async HTTP client |
| `db/schema.sql` | Source of truth: 6 tables, WAL, indexes |
| `db/database.py` | Insert / update / history-on-change helpers |
| `scripts/verify_sold.py` | Reconcile `status='sold'` rows against 999.md (delete genuinely-gone, revert false positives) |
| `web/app.py` | FastAPI app + static mounts |
| `web/queries.py` | Parameterised SQL builder for /api/listings |
| `web/static/index.html` | UI shell |
| `web/static/app.js` | All UI logic (~600 LOC) |
| `web/static/style.css` | Theme + layout |
| `requirements.txt` | httpx, beautifulsoup4, Pillow, loguru, schedule, fastapi, uvicorn |

---

## Storage Layout
```
E:\DB\
  listings.db                    ← SQLite, WAL mode
  photos\
    <listing_id>\
      01.webp, 02.webp, ...      ← 1280×960 max, quality 82, method 2
```

`DATA_DIR` env var lets you redirect anywhere. Default: `E:\DB`. Override:
```powershell
$env:DATA_DIR = "X:/elsewhere"; python pipeline.py --mode full
```

---

## Database Schema
11 tables, all in `db/schema.sql`:

| Table | Purpose |
|------|---------|
| `listings` | Core data (~45 cols incl. `removed_at`, `site_updated_at`, `offer_type`) |
| `photos` | Current photo set; one row per image with `UNIQUE(listing_id, idx)` |
| `price_history` | Append-only on price change |
| `mileage_history` | Dealers sometimes "correct" odometer on relist |
| `description_history` | Edits like "URGENT", "REZERVAT" predict sold-soon |
| `listing_field_history` | **Catch-all**: every scalar field change (33 columns) — `(field, old_value, new_value)` |
| `photo_history` | Photo set diffs — added / removed / replaced events |
| `listing_features` | Many-to-many for optional features (Securitate + Confort) |
| `feature_history` | Append-only feature add/remove events |
| `price_predictions` | Cached ML predictions per active listing — refilled every 24h |
| `scrape_runs` | Per-run telemetry (pages, new, updated, removed, errors) |

Indexes on `status`, `make+model`, `year`, `price_eur`, `last_seen_at`, photo `listing_id`. `PRAGMA journal_mode = WAL` so read-only web UI can coexist with active scrape.

---

## Architecture
```
        ┌───────────────────────────────────────────────────┐
        │              999.md (Next.js SPA)                 │
        │  GraphQL: /graphql (SearchAds op)                 │
        │  SSR:     /ro/<id>  (full spec page)              │
        │  CDN:     i.simpalsmedia.com/999.md/BoardImages/  │
        └─────────────┬──────────────────────────┬──────────┘
                      │                          │
                      ▼                          ▼
        ┌──────────────────┐         ┌──────────────────────┐
        │ crawler.py       │         │ session.py           │
        │ (POST graphql)   │         │ Site sem: 8 polite   │
        │  → list of IDs   │         │ CDN sem:  32 fast    │
        └────────┬─────────┘         └──────────────────────┘
                 │                              ▲
                 ▼                              │
        ┌──────────────────┐                    │
        │ pipeline.py      │ ─── new IDs ──── parser.py
        │  - DISCOVER      │                    │
        │  - DIFF (set)    │ ─── photos ───── photo.py
        │  - SCRAPE NEW    │                    │
        │  - MARK SOLD     │                    ▼
        └────────┬─────────┘         ┌──────────────────────┐
                 │                   │ E:\DB\               │
                 └──────────────────►│  listings.db (WAL)   │
                                     │  photos/<id>/NN.webp │
                                     └──────────┬───────────┘
                                                │ read-only
                                                ▼
                                     ┌──────────────────────┐
                                     │ web/app.py (FastAPI) │
                                     │  /api/listings       │
                                     │  /api/stats          │
                                     │  /api/facets         │
                                     │  /photos/<id>/...    │
                                     └──────────┬───────────┘
                                                ▼
                                     ┌──────────────────────┐
                                     │ vanilla JS frontend  │
                                     │ http://localhost:8000│
                                     └──────────────────────┘
```

---

## Performance Tuning
The default config hits ~30 req/s without 429s.

| Setting | Value | Why |
|---------|-------|-----|
| `CONCURRENT_REQUESTS` | 8 | Polite site pool (999.md HTML/GraphQL) |
| `CDN_CONCURRENT_REQUESTS` | 32 | i.simpalsmedia.com CDN can take it |
| `REQUEST_DELAY_MS` | (200, 600) | Jitter on site only |
| `CDN_DELAY_MS` | (0, 50) | Near-zero on CDN |
| `WEBP_METHOD` | 2 | 3–5× faster encode vs 4; size diff negligible |
| `WEBP_QUALITY` | 82 | Sweet spot |
| `PHOTO_MAX_SIZE` | (1280, 960) | Originals are ~3000px, this is plenty |

**Benchmark**: 156 listings + 2,336 photos in **70 s** (was 510 s pre-optimization). Projected full 88k crawl: **~11 h** (down from ~80 h).

---

## Run & Build
```powershell
# Install
pip install -r requirements.txt

# One quick test pass (top 2 pages)
python pipeline.py --mode quick --max-pages 2

# Full sweep (everything)
python pipeline.py --mode full

# Refresh known listings to track price/mileage/desc changes
python pipeline.py --mode full --refresh-known

# Continuous background scheduler
python scheduler.py

# Web UI (read-only, safe alongside scraper)
python -m uvicorn web.app:app --reload --port 8000
# → open http://localhost:8000
```

---

## Web UI Features
- **Grid + table views** (toggle), Newest/Price/Year/Mileage/Days-listed/Recently-sold sort
- **Cascading filters**: Make → Model dropdown updates on selection
- **Range sliders**: year / price / mileage / engine (currency-aware EUR↔MDL)
- **Multi-select chips**: fuel, transmission, drive, body, color
- **Detail modal**: 10–20 photo gallery (← → arrow keys), 40+ spec rows, inline SVG sparklines for price/mileage history, "Open on 999.md" button
- **Dashboard**: bar charts (top makes, avg price/make, fuel dist, listings-per-day), price-drop leaderboard, sold-this-week
- **Favorites** (localStorage), URL-hash state (shareable links), keyboard shortcuts (`/` search, `Esc` close, `←/→` photo nav)
- **Mark/bookmark** — ★ button on cards; gold contour on marked listings; server-side persistence (`marks.json`) across devices
- **KPI auto-refresh** — top-bar stats poll every 30s with slide-up animation on changed values
- **"Hide ordered" toggle** — excludes `La comandă` / `Auto la comandă` listings using structured fields (no description parsing)
- **Sold dates** on removed listing cards (`sold dd/mm/yyyy · Xd listed`)
- **Theme**: light / dark / auto (system)
- **Mobile**: sidebar drawer at ≤900 px

---

## Analytics & ML (2026-05-19)

- **`web/analytics.py`** — 7 endpoints feeding the Dashboard tab: KPIs, days-to-sell-by-make, drop effectiveness, value retention, sell-through heatmap, DOW trends, stuck inventory. All 60s-cached, outlier-filtered, single-pass GROUP BY (kpis 9.5s → 477ms after rewrite).
- **`web/ml.py`** — sklearn Ridge pipeline (XGBoost auto-detected) for fair-price + days-to-sell. Daemon thread retrains every 24h. Gated below `MIN_TRAINING_ROWS=500` archived listings. Pickled to `E:\DB\models\`. **Sanity filter applied at both training AND inference**: `year IS NOT NULL, year ∈ 1980-2030, mileage_km ∈ 1000-500000, price_eur ∈ 500-200000`. Deal flags clamped to `-90% < delta < 500%`.
- **Frontend** — 5 tabs: Browse (with Deals filter + DEAL/PRICEY card badges) / Dashboard (12 cards w/ Chart.js, 240px-bounded `.chart-box`) / **Analysis** (one combined live-update predictor + verdict tile + filterable hot-deals feed + "How does this work?" explainer) / **Sell-through** (ranked table of every (make, model, year_bucket, fuel, mileage_bucket) combo by sell-through %, top 40 makes, year chip filter, sortable columns) / Favorites (header stats + sort + grid/list toggle). Non-Browse tabs use full page width via `body[data-tab]` CSS rule.
- **Current** (post-cleanup): R²=0.873, MAE=€2,193 on 406 valid rows. ~18k active listings flagged as deals.

## Scraper Speed (2026-05-19 late)

- **`--fast` flag**: sem=12, delay=(50,150ms), HTTP/1.1, 24-thread parse pool. Calibrated to 999.md's measured soft-throttle (sem=24 caused p50 latency to jump from 1s to 13s — they slow-respond instead of 429).
- **`--shard N/M`**: parallel processes with manifest-shared discovery. Available but generally NOT recommended — 999.md throttles per IP, so sharding from one machine splits the same pipe N ways. Empirically slower than `--fast` alone.
- **`--refresh-older-than HOURS`**: incremental refresh. Steady-state nightly run with `--refresh-older-than 24 --fast` finishes in ~15 min instead of 4.5h full sweep.
- **Fast-path in `db.update_listing`**: when no fields changed (the common case), skip the 40-column UPDATE + feature DELETE/INSERT entirely. Just bump `last_seen_at` + `last_fetched_at`.
- **`scripts/run_parallel.ps1`**: PowerShell helper for the rare parallel case.
- **Realistic throughput ceiling**: ~5-6 listings/s single-process (999.md soft-throttles harder concurrency). Full refresh ~4.5h, incremental nightly ~15 min.

## Deployment Plan (planned, not yet executed — 2026-05-22)

Local single-machine setup → publicly-hosted site. The 150 GB data splits cleanly: ~1 GB DB + ~149 GB photos. Photos are static cold blobs; DB is small + hot.

| Component | Where | Why |
|---|---|---|
| **Photos** (~149 GB webp) | Cloudflare R2 public bucket, served as `<img src>` directly | ~$2.25/mo storage, **zero egress** — image traffic would dominate any traditional cloud bill. One-time `rclone sync E:\DB\photos r2:bucket`, then `scraper/photo.py` uploads each new webp inline after WebP encoding. |
| **SQLite** (~1 GB) | Litestream-replicated to R2; VPS reads a hot mirror | Sub-second freshness, read-only on the server. `web/app.py` already opens DB via `file:...?mode=ro` so it drops in with no code change. |
| **Web app** | Hetzner CPX11 (€4/mo, 40 GB disk) running Caddy + uvicorn | Disk is plenty since photos live in R2 and DB is 1 GB. |
| **Scraper** | Stays on local Windows machine | 999.md soft-throttles per-IP; a fresh cloud IP would mean rebuilding the throttle calibration and risking blocks. Local keeps the residential IP and feeds R2 + Litestream as append-only sinks. |

Projected total: **~$7/mo**. Path: provision R2 → bulk-upload photos → wire scraper R2 upload → install Litestream local+VPS → deploy Caddy + uvicorn → swap frontend image URLs to R2.

---

## Notes & Gotchas
- **999.md is a Next.js SPA** — listing pages have a shell only. Use GraphQL `SearchAds` op (subCategoryId 659 = cars) for discovery. Detail pages ARE SSR-rendered so HTML parsing works there.
- **Always strip `<script>`/`<style>` before extracting text** — otherwise i18n JSON dumps end up in fields (location, description). Parser does this in `parse_listing()`.
- **Photos at `i.simpalsmedia.com/999.md/BoardImages/900x900/<hash>.jpg`** — request 900×900 variant for highest quality.
- **`status='running'` scrape_runs orphan if process killed** — finish_run only fires on clean exit. Cosmetic issue, no data corruption.
- **Two concurrent `pipeline.py` processes will compete** on the SQLite file. Kill stragglers before re-running.
- **Web app opens DB read-only** (`file:...?mode=ro` via URI) — guaranteed not to block writes from the scraper.
- **`KEEP_RAW_HTML = False`** by default — keeps DB lean. Flip during dev to debug parser regressions.
- **Price selectors must be SPECIFIC** — use `[class*="price__main"]` for main and `[class*="oldprice__value"]` for the crossed-out discount. The wrapper `[class*="price"]` also contains "Prima rată: 100 €" (down-payment for credit deals) and will get matched first by `select_one`, giving a 100 € price instead of the real value.
- **"Sold" means "no longer in active GraphQL feed"** — covers expired, sold, hidden, or deleted. To distinguish, fetch the URL and check for "Anunțul nu a fost găsit" (truly deleted) vs full spec page (false positive). `scripts/verify_sold.py` does this; pipeline runs it automatically on each full crawl.
- **Editing parser code does NOT update a running scraper** — Python imports are cached per-process. Always restart background scrapers after parser changes.
- **Nothing is hard-deleted anywhere** (2026-05-19): `verify_sold.delete_listing` was a hard `DELETE + shutil.rmtree` that destroyed 235 listings before we caught it. Now soft-archives to `status='removed'` + `removed_at`. Pipeline hot-backs-up `listings.db` to `E:\DB\backups\` before every `--mode full`. The pipeline run-summary no longer prints `listings_deleted` (legacy alias; triggered PTSD).
- **999.md soft-throttles by slow responses, not 429s** — at sem=24 their p50 response time jumped from 1s to 13s. Empirical concurrency ceiling is ~12-16. Pushing harder gets you slower, not faster.
- **Default-arg `config` reads are import-time** — `Session(site_concurrency=config.X)` evaluates the default at class definition; later mutation of `config.X` (e.g. in `--fast`) has no effect. Always read inside `__init__`. This silently broke `--fast` for a while.
- **Junk inputs distort ML output even when training R² looks fine** — pre-filter listings (sane mileage/price/year ranges) at BOTH training AND inference. Otherwise seller-typo rows (10M km mileage) produce headline "deals" that are actually nonsense.
- **CDN does better on HTTP/1.1 than HTTP/2** — i.simpalsmedia.com returned `StreamReset error_code:1 remote_reset` once we pushed h2 concurrency past ~40. Switched httpx to `http2=False`; many TCP connections, no protocol errors.
- **lxml is now the default BS4 parser** — falls back to `html.parser` if missing; pinned in `requirements.txt`. Parse time per listing: ~150 ms → ~40 ms.
- **ML cold start**: `/api/ml/status` returns `{trained: false}` until 500 archived listings exist. Frontend Analysis tab shows a progress card with retraining instructions until then.
- **`price_predictions` table grows stale** between 24h retrains — new listings added in that window don't have flags until the next retrain. Acceptable.
- **pHash failure must write a sentinel, not NULL** (2026-05-22) — `_phash_for` failures use `PHASH_FAILED = -1` (all-ones bit pattern). Backfill query is `WHERE phash IS NULL ORDER BY listing_id LIMIT N`; anything left NULL gets re-picked every batch *forever*. Burned 8 h looping on a single 0-byte webp before catching it. `find_cluster_for_photos` filters `phash IS NOT NULL AND phash != -1` on both sides.
- **"Cumpăr" (buyer) listings are hidden everywhere via `_NOT_BUYER`** (2026-05-23) — `offer_type = 'Cumpăr'` means the poster wants to BUY a car, not sell ("Cumpăr orice marcă, plătesc cash"). Useless noise for a marketplace viewer. Single SQL fragment `(offer_type IS NULL OR offer_type != 'Cumpăr')` is composed into `web/app.py:_status_where` so every status-filtered query inherits it; `web/queries.py:build_listing_query` adds it as a global WHERE. `pipeline.py:_scrape_one` skips `save_photos()` for these but still inserts the row (otherwise discovery re-fetches the HTML every sweep). When adding new endpoints that hit `FROM listings`, either go through `_status_where` or AND `_NOT_BUYER` explicitly.
- **Modal gallery frame is height-driven, NOT aspect-ratio-driven** (2026-05-23) — `.main-photo` is `width:100%; height:100%; max-height:92vh` with img using `object-fit: contain`. Don't reintroduce `aspect-ratio` here without ALSO clamping the other axis: the modal's grid track is `minmax(0, 1.1fr)` which resolves preferred size from content, and `aspect-ratio + width:100%` collapses to the image's intrinsic dimensions, blowing out the modal. Arrows are positioned absolute against `.main-photo` (which has `position: relative`) so they stay pinned across portrait↔landscape swaps.
- **`web/analytics.py` must apply `_NOT_BUYER`** (2026-05-23) — `web/app.py` strips `offer_type = 'Cumpăr'` globally via `_status_where` + `build_listing_query`, but analytics endpoints used to run raw `WHERE status='active'` queries. Result: model-stats card showed 89,635 active while the top-bar KPI showed 86,169 — a 3,466 buyer-side inflation. Fix: module-level `_NOT_BUYER = "(offer_type IS NULL OR offer_type != 'Cumpăr')"` at the top of `analytics.py`, folded into `REMOVED_FILTER` and every `active`/`sold_*` query. When adding new analytics endpoints, AND it in by hand or counts will diverge from the rest of the app.
- **Cluster-merged price history lives in `/api/listings/{id}`, NOT a separate endpoint** (2026-05-23) — `get_listing()` fetches `price_history` + `mileage_history` from EVERY sibling in the `car_identity` cluster and returns them as one chronologically-sorted list tagged with `listing_id` per point. This replaces the per-listing series when a cluster exists. The frontend chart colors points by listing id so relisting boundaries show. Don't add a `/api/listings/{id}/cluster_history` endpoint — the merge happens in one read, payload size is small (most clusters have ≤6 listings × ≤4 price points each).
- **"Sold" tabs/counts exclude relisted-active twins** (2026-05-23) — when a removed listing's `car_identity_id` has at least one sibling with `status='active'`, the seller just refreshed the post — the physical car isn't sold. `web/queries.py` adds `NOT EXISTS (SELECT 1 FROM listings sib WHERE sib.car_identity_id = listings.car_identity_id AND sib.status='active')` to the Removed/Sold WHERE clause. `analytics.model_stats` mirrors this with `sold_recent_truly` / `sold_total_truly` fields; the raw counts (`sold_recent`, `sold_total`) remain so the info-tooltip can surface the gap.
- **Unique-car Active count uses `COUNT(DISTINCT COALESCE(car_identity_id, -id))`** (2026-05-23) — collapses cluster siblings to one bucket while leaving standalone listings (NULL identity) intact. Negating `id` guarantees a standalone key can't collide with a positive cluster id in the same DISTINCT bucket. Headline shows unique cars; `active_total_listings` + `active_duplicates` power the info tooltip.
- **Chart.js time scale needs `chartjs-adapter-date-fns`** (2026-05-23) — detail-modal price/mileage charts use `type: 'time'` so ISO recorded_at strings render with proper date ticks. Bundle: `<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js">`. With `parsing: false` the scale skips the adapter — leave parsing on (default) when feeding ISO strings.
- **Scrollbars must reference theme tokens** (2026-05-23) — `::-webkit-scrollbar-thumb { background-color: var(--border-strong) }` blends across light + dark without per-theme overrides. The slim 8px variant for `.detail-card`, `.filters`, `.thumbs` uses `var(--border)` (lighter) so the three high-contrast bars (modal scroll + filter rail + thumbnail strip) recede. Firefox: `scrollbar-color: var(--border-strong) transparent; scrollbar-width: thin` on `html`. Default Windows chrome looked stamped-on against `#161618` panels.
- **Cluster matching has two guardrails: template-phash exclusion + make+model gate** (2026-05-24) — `db/database.py:find_cluster_for_photos` excludes phashes that span `≥ PHASH_TEMPLATE_MIN_MAKE_MODEL_SPAN` (=2) distinct (make, model) values (dealer overlays / placeholders / watermarks) and restricts the candidate scan to same make+model. Without these guardrails, **dealer template phashes alone caused 78/1295 multi-member clusters to mix makes** (e.g. cid=2892 merged Toyota Yaris + Skoda Octavia + BYD Song + Suzuki Vitara + BMW X7 + Mercedes Vito + Citroen + Peugeot + Opel into one "cluster" via shared idx=2/idx=3 template frames). The top placeholder phash appeared in 13,860 listings (14% of DB). **Definition by make+model SPAN, not by absolute frequency** — a legit car relisted 5+ times has photos that appear 5+ times but only in one (make, model), so absolute-frequency filtering wrongly broke real clusters (e.g. Peugeot 3008 ×6). The span rule is information-theoretically clean: a unique car photo can only belong to one make+model.
- **`scripts/reset_clusters.py`** (2026-05-24) — wipes `car_identity` + resets `listings.car_identity_id` / `relisted_from_listing_id`. Use after the algorithm changes so a fresh `--phase cluster` backfill rebuilds from scratch. Idempotent. Safe with web/app.py running (it reads NULL clusters as standalone listings, no UI break).
- **`idx_listings_car_identity` is mandatory once clustering covers most rows** (2026-05-24) — the cluster-dedup `NOT EXISTS` subquery in `web/queries.py` only stays fast when there's a composite index on `(car_identity_id, status, first_seen_at)`. While clustering covered just 5.7% of listings (pre-2026-05-24 backfill), the `car_identity_id IS NULL` shortcircuit handled 94% of rows and the subquery rarely ran. After the backfill 100% of rows have non-NULL `car_identity_id`, so the subquery runs for every row and a missing index makes the items query hang for tens of seconds. Schema now includes the composite; on existing DBs, `db.init_db()` migration picks it up via `CREATE INDEX IF NOT EXISTS`. EXPLAIN should show `SEARCH sib USING COVERING INDEX idx_listings_car_identity (car_identity_id=? AND status=?)`.
- **WAL bloat needs a manual `wal_checkpoint(TRUNCATE)` after mass-mutation runs** (2026-05-24) — assign_cluster on 99k rows + reset + re-assign grew WAL to 3.3 GB while the web app was actively reading. Auto-checkpoint can only truncate up to the earliest open reader, so constant web requests pin it. Fix: stop the web app, run `PRAGMA wal_checkpoint(TRUNCATE)` from a fresh write connection, restart web. Steady-state scraping doesn't cause this — only large one-shot operations.
- **`assign_cluster` has a defensive cross-make/model guard** (2026-05-24) — refuses to join a cluster when both the new listing AND the matched prior have non-NULL (make, model) AND they disagree. Belt-and-suspenders on top of `find_cluster_for_photos` so any stale in-memory code path (e.g. a long-running `scheduler.py` daemon that imported the pre-patch module) cannot produce chimeras even by accident. Falls back to a fresh singleton instead. Discovered necessary when 2 cross-make clusters formed during the 2026-05-24 backfill despite the find_cluster gate — root cause was a concurrent long-running scrape using the pre-patch `db.database` module from memory. **When changing `db/database.py` cluster logic, also restart `scheduler.py` / any long-running scrape process** — Python doesn't auto-reload imports.
- **`scripts/dissolve_chimeras.py`** (2026-05-24) — finds clusters whose members have multiple distinct non-NULL (make, model) values and dissolves them by evicting minority members into singletons. Idempotent. Conservative — leaves `Make/None vs Make/Model` clusters alone (likely real same-car merges with a parser miss).
- **Final cluster-quality scorecard after 2026-05-24 fix run**: 99,458/99,458 listings clustered (100%); 83,371 clusters total; 12,893 multi-member (true relists); mixed-make went from 78 → 2 (−97%); mixed-make+model went from 104 → 8 (−92%, of which 6 are NULL-model not true chimeras). Top clusters are coherent dealer fleets — Hyundai Tucson ×82, Peugeot 3008 ×32, BYD models ×24 each.
- **Cluster step is gated on `is_new=True`** (2026-05-24) — `pipeline.py:309-326` only calls `find_cluster_for_photos` + `assign_cluster` when the listing is being inserted for the first time. Refresh visits skip clustering entirely. Consequence: every listing that landed in the DB before clustering was wired up stays `car_identity_id IS NULL` forever — they never get a chance to match against anything. Caught on 2026-05-24 when **96,326 / 99,054 (97.2%) of listings were unclustered** despite 100% of 1.16M photos having valid phashes. Fix is `python -m scripts.backfill_phash --phase cluster` as a one-shot. Self-healing alternative: also call `assign_cluster` on the refresh path when `car_identity_id IS NULL`.
- **`--phase hash` is permanently idempotent after first backfill** (2026-05-24) — `scraper/photo.py:_encode_webp` writes phash inline on every new download (real value or `-1` PHASH_FAILED sentinel on error), so `WHERE phash IS NULL` returns 0 rows in steady state. "Nothing to hash" is **expected and correct**, not a bug. If you're trying to fix missing clusters, you want `--phase cluster` (matches existing phashes into car_identity rows), NOT `--phase hash`. The two phases are unrelated work: hash computes per-photo fingerprints, cluster builds cross-listing identity from them.
- **`seller_id` is NULL for ~98% of listings** (2026-05-24) — parser isn't extracting seller info from 999.md detail pages reliably; only 1/90 Corolla candidates had it populated. Blocks any "seller + specs" duplicate-detection fingerprint. Phone-number capture (already on todo) would be a stronger signal anyway since 999.md hides it behind an "Arată numărul" GraphQL call.
- **New filter toggles must be wired through BOTH `web/queries.py` AND `web/analytics.py:build_extra_filters`** (2026-05-26) — the Browse grid and the model-stats side-card use different query builders. If a toggle (like `hideOrdered`) only goes through `queries.py`, the grid shows N listings but the side-card shows a different Active count. The `model_stats` endpoint in `app.py` passes all non-stripped params to `build_extra_filters`, so adding the handling there is enough — but you must remember to add it. Test: toggle the filter, compare grid's "X listings" with the side-card's Active tile. They must match.
- **Sell-through tab groups by year_bucket, NOT generation text** (2026-05-27) — the `generation` column from 999.md is free-text and often NULL. Using it for grouping created tiny misleading buckets (e.g., 7 NULL-generation Honda Accords with 100% sell-through while the real cohort had 54 active). Fix: always group by `_year_bucket(year)` which uses fixed 5-year windows (2014-2018, 2019-2023, 2024+). The `_generation_label()` helper still exists for other uses but the sell-through page ignores it. Mileage: two buckets only (0-100k / 100k+). Top 40 makes by volume; smaller makes excluded to reduce noise. Active count uses cluster dedup (same as Browse's model_stats).
- **`_dedup_sql()` refactored into `_cluster_dedup_sql()` + `_dedup_sql()`** (2026-05-27) — the relisting filter (exclude sold listings with active siblings) and the cluster dedup (keep newest per car_identity) were previously tangled into one inline SQL block inside `model_stats()`. Now extracted as module-level `_cluster_dedup_sql(pfx)` and `_dedup_sql(pfx)` helpers. The `pfx` param generates `listings.col` (default) or `l.col` for aliased queries. **Critical bug found during refactor**: `_dedup_sql("")` initially generated unqualified column names (`car_identity_id` without prefix) — inside a NOT EXISTS subquery, SQLite resolves these to the innermost scope (`sib.car_identity_id`), making `sib.car_identity_id = car_identity_id` always true and excluding ALL rows. Fix: default prefix is `"listings."` not `""`.
- **Browse model_stats `sold_total_truly` now applies cluster dedup** (2026-05-27) — previously only applied the relisting filter but not the cluster dedup, so stats showed 14 sold while the grid showed 4 listings for the same Honda CR-V filter. Both now use the same `_dedup_sql()` which combines both filters.
- **`sqlite3.connect(timeout=30)` on all write connections** (2026-05-27) — `db/database.py:connect()` and `init_db()` had no `timeout` param, so SQLite gave up instantly on lock contention (`database is locked`). The web server's read-only connection via WAL can still briefly block writers during checkpoint. Adding `timeout=30` makes SQLite retry for up to 30 seconds instead of crashing. Affects both the pipeline and any future write callers.
- **Sell-through formula = `sold_truly / (active + sold_truly)`** (2026-05-23) — denominator is "cars that touched the market in the window", numerator is the truly-sold count. NOT `sold / total_listings_ever` (would always trend to 0 over time) and NOT `sold / active` (could exceed 100% which is meaningless). Computed client-side in `renderModelStatsCard()` because all three inputs (`active`, `sold_recent_truly`, `recent_days`) already arrive in the same payload. If you add backend cohort filters that affect these numbers, the tile auto-updates — no extra wiring. Display tiers `≥10%` int, `1–10%` one decimal, `>0 <1` → `<1%` (real-but-tiny sell-through must not read as 0%).

---

## Backup Log
See [[../chat-history/999-CarScrapper-chats|Chat History]] · [[../decisions/999-CarScrapper-decisions|Decisions]] · [[../todo/999-CarScrapper-todo|Todo]]
