# 999 CarScrapper — Design Decisions

> WHY things were built the way they are.

---

## 2026-05-28 — Discovery and refresh split into two processes

**Decision**: `scheduler_f.py` is locked to **discovery + new-listing detection only** (tick every 10 min). All refresh work moved to a separate `refresher_loop.py` that runs `pipeline.run(mode="full", refresh_known=True)` continuously. The two processes coordinate only through SQLite WAL — no IPC, no shared locks beyond per-commit serialization.

**Why**: Previously scheduler_f handled both: tick (every 10 min, fast) + incr (twice daily) + full (Sunday weekly). The user wanted refresh-known to run continuously, not on a slow cadence. Folding "continuous refresh" into scheduler_f would mean the tick — the only thing that catches new listings within 10 min — could be blocked by a multi-hour refresh pass. Splitting processes keeps the new-listing latency budget intact.

**How to apply**: when one job has a tight latency SLO (tick: must fire every 10 min) and another is throughput-bound (refresh: runs for ~30–60 min per pass), don't put them in the same scheduler. Separate processes + SQLite WAL is cheaper than coroutine-juggling them in one.

---

## 2026-05-28 — Per-chunk DB connection sharing + per-listing commit

**Decision**: Workers in a chunk share one `db.connect()` for the lifetime of that chunk (~2000 listings), BUT `conn.commit()` runs after every worker's writes — not once at chunk end.

**Why**: First iteration committed only at chunk end to maximize savings. That held the SQLite write lock for the full ~17 min chunk and starved the scheduler's tick → `database is locked` after the 30 s connect timeout. WAL allows many readers but only one writer; transactions held that long are toxic in a multi-writer system. Per-listing commit costs ~1-2 ms WAL fsync; per-listing connect/close costs ~3-5 ms. Net: still faster than the old "fresh conn per listing" path, but the write lock is released between every listing so the scheduler can interleave.

**How to apply**: Sharing a SQLite connection across many ops in a multi-writer system is fine — sharing a TRANSACTION isn't. Commit early, commit often. The connect savings are the speedup; the held transaction was a bug, not the feature.

**Risk**: If anyone later adds an `await` inside the worker's DB section, two writes could interleave on the same connection and produce a partial transaction. Document this constraint at the call site.

---

## 2026-05-28 — Refresher MUST skip discovery + new-listing inserts

**Decision**: `refresher_loop.py` calls `pipeline.run(skip_discovery=True, skip_backup=True)`. Refresher only re-fetches existing rows; scheduler_f.py is the sole process that crawls GraphQL and inserts new IDs.

**Why**: Initially tried letting refresher run the full `--mode full --refresh-known` codepath in parallel with the scheduler. Caused silent data loss: both processes did `INSERT OR REPLACE INTO listings` for the same new IDs, and `ON DELETE CASCADE` on every child table meant the second writer wiped the first's photos + history. See [[mistakes#2026-05-28 — INSERT OR REPLACE]].

**How to apply**: When designing parallel writer processes against the same SQLite DB, partition the WRITE responsibilities, not just the read responsibilities. One process per UPSERT target. SQLite WAL's "concurrent writers" guarantee is about serialization, not about isolation from cascade side-effects.

---

## 2026-05-25 — Marks stored server-side in JSON, not localStorage or SQLite

**Decision**: The new "mark a listing" feature (gold contour) persists marks in `E:\DB\marks.json` via three FastAPI endpoints (`GET/POST/DELETE /api/marks/{id}`). File I/O is protected by a `threading.Lock`. Frontend loads marks at init and toggles them instantly.

**Why**: Three options were on the table:
1. **localStorage** (like favorites) — same-device only; user explicitly wanted cross-device persistence.
2. **SQLite column/table** — the web app opens the DB read-only (`file:...?mode=ro`) to avoid blocking the scraper. Adding a writable connection just for marks would break that safety guarantee.
3. **JSON file** — writable, no DB contention, trivially portable (copy one file). The marks set is tiny (tens of IDs), so JSON serialization is instant. File lives in `DATA_DIR` alongside the DB, so it's included in any backup/migration of the data directory.

**How to apply**: when adding a user-preference feature to a read-only-DB app, don't introduce write access to the main DB. A sidecar file (JSON, TOML, SQLite in a separate path) keeps the safety boundary clean.

---

## 2026-05-25 — "Recently sold" sort auto-selected on Removed tab

**Decision**: Added `sold_at` to `ALLOWED_SORTS` in `web/queries.py` as `COALESCE(removed_at, sold_at, last_seen_at)`. New `<option value="sold_at:desc">Recently sold</option>` in the sort dropdown. When the user clicks "Removed" in the status toggle, `app.js` auto-switches sort to `sold_at:desc`; switching back to Active reverts to `first_seen:desc`.

**Why**: "Newest first" sorts by `first_seen_at` — when the listing was first posted, not when it was removed. On the Removed tab, a listing posted May 20 and removed May 21 ranked above one posted May 19 and removed May 23. Users expected "newest" to mean "most recently sold." Rather than changing the meaning of "Newest first" (which would confuse Active-tab users), we added a separate sort and auto-select it contextually.

**How to apply**: when a sort label's meaning is ambiguous across tabs/contexts, add a context-specific sort and auto-select it on tab switch rather than changing the existing sort's behavior. Revert on tab-switch-back so the user's Active-tab preference isn't lost.

---

## 2026-05-25 — Sold date displayed on listing cards (bottom row)

**Decision**: Card bottom row now shows `sold dd/mm/yyyy · Xd listed` for removed/sold listings. New `fmtSoldDate(iso)` helper formats the ISO date. Uses `it.sold_at || it.removed_at` from the existing API response — no backend change needed.

**Why**: The circled spot in the card already showed "Xd listed" (days since first_seen_at). For removed listings, the user wanted to know WHEN it was sold, not just how long it was listed. The sold date answers "is this market data recent?" at a glance without opening the detail modal.

**How to apply**: card-level metadata should answer the question "should I click this?" — timestamps of key lifecycle events (listed, sold) are high-signal for that decision.

---

## 2026-05-23 — Prank-price filter (≥35% drop from first asking) + dynamic "All listings" stat panel

**Decision**: In `web/analytics.py:model_stats`, average sold/active prices exclude any listing whose final (or current) price is ≤65% of the original `price_history` row for that listing. Threshold lives in a single constant `PRANK_DROP = 0.35`. The same function now accepts optional `make`/`model` — when both omitted, stats run over every listing matching the sidebar filters. The Browse side-card always renders during filtering (no longer gated on make+model selection).

**Why**:
1. **Prank/typo rows skew averages catastrophically** — sellers sometimes edit price to "100 €" as a placeholder (or to bump the listing in feeds). A single 30 k → 100 € edit drops the cohort average by thousands. The 35% cutoff is well outside any realistic sale-negotiation discount (10-15% is normal) yet wide enough that legitimate steep cuts on stuck inventory still count. Computed against the listing's own original price rather than a cohort median so the heuristic is local to each ad and immune to cohort-size effects (a 2-listing cohort has no useful cohort median).
2. **Same logic for sold and active** — user wants symmetric tiles; same prank filter applies because active listings can also be mid-edit when scraped.
3. **Tooltip reveals what was excluded** — the "i" hover shows "Excludes N listings priced ≥35% below original asking price. Average of all: €X". Without this transparency a user comparing the side-card to the visible cards would assume a bug.
4. **Stats panel must work without make/model** — the user explicitly wanted the price summary on any filter change (year/fuel/transmission/price-range alone, no model picked). Old behaviour hid the card unless both were set, which made the panel useless for early exploration. Made make/model query params optional rather than adding a sibling endpoint, since 95% of the SQL was identical.

**Original bug that started this**: the SQL `ORDER BY price LIMIT 1 OFFSET COUNT/2` median was off-by-one for even counts (returned the upper middle instead of averaging the two middles). User was the first to catch a 27500 vs real-median-25249.5 mismatch on a 4-listing cohort. Final implementation moved median calculation Python-side, then was replaced by an average per user preference.

**How to apply**: Whenever a marketplace stat aggregates user-edited prices, check for placeholder edits (1 €, 100 €, "Prima rată" down-payment substrings). Compare each row's final price to its own first-recorded price rather than to the cohort — the per-listing baseline is robust to small cohorts and to genuine cohort-wide price shifts. Always surface what was excluded via a tooltip; silent filtering breeds distrust.

---

## 2026-05-23 — Hide "Cumpăr" (buyer-side) listings everywhere; skip photo download for them

**Decision**: Listings with `offer_type = 'Cumpăr'` (sellers posting "I want to BUY a car") are filtered out of every UI endpoint via a single SQL fragment `_NOT_BUYER = "(offer_type IS NULL OR offer_type != 'Cumpăr')"`, composed into `_status_where` in `web/app.py` and added as a global WHERE in `web/queries.py:build_listing_query`. `pipeline.py:_scrape_one` skips `save_photos()` when `offer_type == 'Cumpăr'` but still inserts the row.

**Why**: 3,644 Cumpăr rows were polluting the Browse grid and inflating dropdown counts — they're irrelevant noise for a marketplace VIEWER (you can't buy a car from someone who's also looking to buy). Three pressures shaped the design:
1. **Hide everywhere, not just the main grid** — a Cumpăr-only make would otherwise leak into the Make dropdown via `/api/facets`. Centralising the predicate in `_status_where` propagates to facets/models/stats without touching every query.
2. **Don't redownload photos for them** — already wasted ~3 GB of disk + CDN budget on existing Cumpăr photos. Future scrapes skip `save_photos()` after parse identifies the offer_type.
3. **Don't re-fetch the HTML every sweep either** — the row still gets inserted so discovery's known-ID set covers it. If we skipped insert entirely, every `--mode full` would re-parse the same Cumpăr HTML forever.

**How to apply**: When you need to permanently exclude a subset from a read-heavy app, put the predicate in ONE place (a constant + the helper that builds status fragments). Audit `Grep("FROM listings.*WHERE")` to find queries that bypass the helper and patch them too. Don't soft-delete via `status='ignored'` — it complicates the existing soft-archive state machine (`active`/`sold`/`removed`); a separate column-level predicate is cleaner.

---

## 2026-05-22 — Sentinel value (`-1`) for unhashable photos instead of NULL or separate column

**Decision**: When `imagehash.phash` fails (corrupt webp, missing file, zero bytes), write `PHASH_FAILED = -1` into `photos.phash` rather than leaving it `NULL` or adding a `phash_failed BOOL` column.

**Why**: The backfill query is `WHERE phash IS NULL ORDER BY listing_id LIMIT N`. Anything that leaves a row at NULL gets re-picked every batch forever — we burned 8 hours looping on one 0-byte file before catching it. A sentinel makes the row leave the queue with zero schema changes. Bit-pattern is all-ones (signed `-1`, unsigned `0xFFFF...FFFF`); collision with a real phash is 1/2^64. Cluster matching explicitly excludes it on both sides (`phash IS NOT NULL AND phash != -1`).

**How to apply**: Any long-running backfill keyed off `WHERE col IS NULL`: pick a sentinel that's clearly out-of-band (here, all-ones for a hash whose real values are uniformly distributed; for IDs use a negative number; for timestamps use a far-past date). Writing on failure costs one column update and saves a schema migration. Pre-sweep known-bad rows before the backfill starts — we found all zero-byte files (1 in 933 k) and stamped them before kicking the run.

---

## 2026-05-22 — Deployment plan: photos to Cloudflare R2, DB via Litestream, web app on small Hetzner VPS

**Decision**: When the site goes live, split the 150 GB local data into two sinks. Photos (~149 GB of webp) → Cloudflare R2 public bucket, served as `<img src>` directly. SQLite (~1 GB) → Litestream-replicated to R2, read-only mirror on a €4/mo Hetzner CPX11. Scraper stays on the local Windows machine.

**Why**: Three forces pulled the design:
1. **R2 has zero egress** — cars are mostly photo views, and CDN-style image traffic on any traditional cloud would dominate cost. R2: ~$2.25/mo storage, free egress.
2. **The DB is the hot mutable thing, photos are cold blobs** — different replication strategies. Litestream streams WAL frames for sub-second freshness; R2 is one-time bulk upload + new-photo inline upload from the scraper.
3. **Scraper must keep its residential IP** — 999.md soft-throttles per-IP. Moving the scraper to a cloud VPS would mean fresh IP blocks and rebuilding the throttle calibration. Local stays local; only the read side ships outward.

Projected monthly cost: ~$7 (€4 VPS + $2.25 R2). Web app already opens DB read-only via `file:...?mode=ro`, so a Litestream replica drops in with no code change.

**How to apply**: For any data-heavy local app with a small mutable index and big static blobs, this split (object storage + replicated SQLite + cheap compute) is dramatically cheaper than a fat VPS or managed Postgres. The trigger is "would my egress dominate?" — if yes, R2 first, everything else after.

---

## 2026-05-18 — Use GraphQL endpoint for listing discovery (not HTML scrape)

**Decision**: Crawler POSTs to `https://999.md/graphql` with operation `SearchAds` instead of fetching `/ro/list/transport/cars?page=N` and parsing HTML.

**Why**: 999.md migrated to Next.js (App Router). The list-page HTML is a shell — listing IDs are fetched client-side via XHR after hydration. Plain `httpx` got 700 KB of HTML with zero IDs. Verified by inspecting `__next_f.push(...)` streamed chunks (only i18n strings, no ad data) and capturing network requests in agent-browser.

**How to apply**: Any modern site built on Next.js/Remix/Nuxt — assume the listing data is NOT in the SSR HTML. Open it in the browser, look at the Network tab, find the actual JSON endpoint, hit that directly. Pagination is usually `pagination: {limit, skip}` not `?page=N`.

---

## 2026-05-18 — Detail pages stay HTML-parsed (still SSR)

**Decision**: Per-listing detail (`/ro/<id>`) parsed via BeautifulSoup, NOT via a separate GraphQL detail endpoint.

**Why**: Detail pages are still server-rendered. Specs (`Marcă BMW`, `Rulaj 150000 km`), photos (CDN `<img>` tags), description (`[itemprop="description"]`) all present in raw HTML. Fast, simple, no extra reverse-engineering work. The detail-page GraphQL ops (`AdSubcategoryUrl`, `AdViews`) only fetch breadcrumb/analytics data.

**How to apply**: Don't assume an entire site uses the same render strategy. List pages and detail pages can differ — check each.

---

## 2026-05-18 — Split semaphores by host (site vs CDN)

**Decision**: `scraper/session.py` has two pools: `_site_sem` (8 concurrent, polite delay 200–600 ms) for `999.md`, and `_cdn_sem` (32 concurrent, near-zero delay 0–50 ms) for `i.simpalsmedia.com`.

**Why**: A single global semaphore + delay was throttling image downloads to the same polite rate as site HTML. Photos dominated the workload (~15 per listing), so the bottleneck was photo concurrency, not site politeness. CDNs are built to handle 30+ concurrent connections.

**How to apply**: When a scraper hits multiple hosts, separate rate limits per host. Static-asset CDNs almost always tolerate way more concurrency than the origin site. Routing by `urllib.parse.urlparse(url).hostname` is enough.

---

## 2026-05-18 — Per-listing photo parallelism + Pillow off the event loop

**Decision**: `scraper/photo.py` uses `asyncio.gather(*[_fetch_and_save(url) for url in urls])` instead of a serial `for` loop, and the Pillow encode is wrapped in `asyncio.to_thread`.

**Why**: A serial loop with 10 photos × ~700 ms delay = ~7 s per listing for I/O alone. Pillow's `Image.open + thumbnail + save` blocks the event loop for ~200 ms per image, so even with parallel I/O, encoding bursts froze workers. Combined fix took a 2-page test from 8.5 min → 70 s (7.2× speedup).

**How to apply**: Any time you `await` in a loop and the work could happen concurrently — use `gather`. Any time a CPU-bound library (Pillow, lxml, json with deep dicts) runs inside an async handler — wrap in `asyncio.to_thread`.

---

## 2026-05-18 — Storage on E:\DB instead of project folder

**Decision**: `config.DATA_DIR = Path(os.environ.get("DATA_DIR", r"E:\DB"))`. Both `listings.db` and `photos/` live there.

**Why**: Project lives on the OneDrive-synced C: drive (Code folder), which would sync the DB + 1 TB of photos to OneDrive and burn quota. E: has 1 TB free and is not synced. Env var override means dev can redirect for tests without touching code.

**How to apply**: For any project that generates large local artifacts (datasets, photos, video, build outputs), keep them off cloud-synced folders. Use an env var so the path isn't hardcoded.

---

## 2026-05-18 — Separate history tables (price / mileage / description), not a single audit table

**Decision**: `price_history`, `mileage_history`, `description_history` as three append-only tables, each writing only when the value actually changed.

**Why**: ML use case — the trajectory IS the feature. A car listed at €7,500 → €7,000 → sold is a different signal from €7,000 → sold. Per-field tables are simpler to query, smaller (only changes append), and let analysis SQL be straightforward (`SELECT MIN(recorded_at), MAX(recorded_at) GROUP BY listing_id`). A single audit table would require parsing JSON for every analysis.

**How to apply**: When fields change independently and you want time-series analysis per field, separate tables beat a single audit log.

---

## 2026-05-18 — Web app opens DB read-only

**Decision**: `web/app.py:db()` uses `sqlite3.connect(f"file:{path}?mode=ro", uri=True)`.

**Why**: The web app should never block or corrupt the scraper. WAL mode allows concurrent readers and one writer, but a read-only connection adds a belt — even a buggy SQL string in a future endpoint can't accidentally write. Also clearer signal of intent.

**How to apply**: Any view-only service on top of a write-heavy data store — open it read-only.

---

## 2026-05-18 — Vanilla JS frontend, no build step

**Decision**: `web/static/{index.html, app.js, style.css}` — three files, no React/Vue/Vite/npm.

**Why**: Single-developer local tool. Build tooling would add `npm install` + `npm run build` + node_modules + Vite config to an otherwise pure-Python project. The UI is ~600 LOC of plain JS, ~400 LOC of CSS — easily fits. No framework benefits matter here (no team, no large state, no SSR).

**How to apply**: Before reaching for React, count the LOC you'd actually write. <1 k LOC of UI = vanilla. >5 k LOC or a team = framework. The middle is judgement; bias to vanilla for local tools.

---

## 2026-05-18 — Always strip `<script>`/`<style>` before any text extraction

**Decision**: `parse_listing()` calls `soup(["script", "style", "noscript", "template"]).decompose()` as the very first step.

**Why**: A bug where `find(string=re.compile("Localitate"))` matched the substring "Localitate" inside a Next.js i18n JSON blob (in a `<script>` tag) wrote the entire 30 KB JSON dump as the `location` field for 1,706 of 1,709 listings. Defence-in-depth: even with specific selectors, future regressions can leak script content. Stripping up-front makes the whole class of bug impossible.

**How to apply**: Whenever you use BeautifulSoup `.find(string=…)`, `[class*="…"]`, or any partial match — strip script/style/noscript/template FIRST. Even if you "know" the selector is specific.

---

## 2026-05-19 — Verify "missing" listings on 999.md before flagging them sold

**Decision**: Pipeline's diff step no longer trusts GraphQL discovery as the sole source of truth. For every ID present in the previous active set but missing from this crawl, fetch the listing URL once and inspect the visible page body:
- contains "Anunțul nu a fost găsit" → genuinely deleted → **DELETE** row + history + photo folder
- still has `[class*="features"] li` (full spec list) → false positive → **revert to active**
- otherwise → mark sold (unrecognised state — keep for manual review)

**Why**: GraphQL `SearchAds` occasionally drops listings that are still alive (paused, hidden from feed, dealer's premium-only inventory). The original diff would have wrongly killed them as "sold". Also: my earlier "expirat" string check was matching the i18n KEY inside a `<script>` tag, not actual page content, so it gave a false sense that the detection was working. Verifying against the real rendered body is the only reliable signal.

**How to apply**: Any set-difference deletion (diff old vs new IDs) should be verified against the source before applying. Cost: N extra HTTP calls per sweep, but N is small (only newly-missing rows). Implementation lives in `scripts/verify_sold.py:page_state()` and is imported into `pipeline.py`.

---

## 2026-05-19 — Use specific class selectors for price, never the wrapping container

**Decision**: Switched from `[class*="price"]` (matches the wrapper containing main + old + installment) to `[class*="price__main"]` (current price) and `[class*="oldprice__value"]` (crossed-out discount price).

**Why**: Original selector matched the wrapper that contains 4 distinct values: main price, old price, discount %, and the "Prima rată: 100 €" down-payment for credit deals. The regex grabbed the first `<num> €` it saw — often the 100 € installment instead of the real 15,990 € price. 191 listings ended up with prices <500 € (many at 1 €). Burnt prices were impossible to detect from data alone since "1 €" can be a legitimate (though ridiculous) listing.

**How to apply**: When a wrapping class name appears in many specialised child elements, the partial selector matches them all. Always inspect the live DOM to find the most specific class for the value you want. Rule of thumb: if `getText()` of your match contains more than one piece of data, the selector is too broad.

---

## 2026-05-19 — Use HTML `hidden` attribute + a `[hidden] { display: none !important }` guard

**Decision**: Added `[hidden] { display: none !important; }` early in `style.css`. The frontend uses `el.hidden = true/false` everywhere instead of class toggles.

**Why**: Setting `display: grid` on `.detail` for the centered modal overrode the user-agent stylesheet's `[hidden] { display: none }`. Closing the modal via `host.hidden = true` left the dark overlay visible and intercepting every click — page looked completely frozen. The single-line CSS guard makes the attribute always win regardless of what specific `display:` rules come after.

**How to apply**: When using HTML `hidden` for state toggles, drop a `[hidden] { display: none !important }` at the top of the stylesheet. Don't rely on the user-agent default — any `display:` rule on the same element will override it.

---

## 2026-05-19 — `ALTER TABLE ADD COLUMN` for schema migrations, not a versioned migration system

**Decision**: When adding `old_price_eur` / `old_price_mdl` to `listings`, ran two `ALTER TABLE listings ADD COLUMN ... INTEGER` statements directly against the live DB and updated `schema.sql` to match for fresh installs. No migration library, no version table.

**Why**: SQLite's WAL mode + nullable column addition is non-blocking and instantaneous regardless of row count. A migration framework (Alembic, etc.) adds a versions table, migration files, downgrade scripts — none of which earn their weight for a single-developer scraper. If a column ever needs to be removed or renamed, do a one-off `CREATE TABLE … SELECT … FROM old` swap.

**How to apply**: For solo SQLite projects, keep `schema.sql` as the source of truth for fresh installs and apply `ALTER TABLE` directly for additive changes on running DBs. Reach for Alembic only when there's a team or a multi-step refactor.

---

## 2026-05-19 — Chunked scrape targets + per-chunk Session recycle to bound memory

**Decision**: `pipeline.run()` iterates scrape targets in batches of `SCRAPE_CHUNK_SIZE` (default 500). Each chunk gets a brand-new `Session` (httpx client) via `async with`, all 500 workers run via `asyncio.gather`, then the session is closed and `gc.collect()` runs. The previous design built a single `asyncio.gather(*tasks)` over all 80k targets upfront.

**Why**: Two compounding leaks. First, the unified gather list held 80k coroutine + Future objects in memory until the entire run completed (~10 h), pinning all intermediate state. Second, httpx's connection pool monotonically grew as the run progressed. Combined, the scraper hit ~13 GB RSS by end of run, which had no headroom on smaller machines and risked OOM. Splitting into chunks lets workers drain, the httpx pool tear down via `aclose()`, and parse trees + photo bytes get released. Result: flat RSS around a few hundred MB across the whole run.

**How to apply**: Whenever the task count grows large enough that the full task graph doesn't fit comfortably in memory (rule of thumb: >10k tasks, or any task that allocates >1 MB transiently), process in chunks. The chunk size should be ~few-minutes of work — big enough that recycle overhead is invisible (~100 ms per recycle), small enough that worst-case memory between recycles is bounded. Use `async with Client()` per chunk so the connection pool genuinely resets, not just an `await client.close()` reused on the same instance.

---

## 2026-05-19 — Soft-archive instead of hard-delete (after the 235-row catastrophe)

**Decision**: `verify_sold.delete_listing(conn, lid)` is now `UPDATE listings SET status='removed', removed_at=datetime('now')` — no row deletion, no `shutil.rmtree`. Function name kept to avoid churning callers; behaviour entirely inverted.

**Why**: The previous implementation actually DELETED rows + recursively removed photo folders for every listing that 999.md's detail page returned "Anunțul nu a fost găsit" for. The user only noticed when a daily sweep reported `listings_deleted=235`. Of 9 surviving orphan photo folders, all were empty shells (rmtree had succeeded) and 999.md returned "not found" for all 9 — unrecoverable. Soft-archive preserves the row, photos, every history table, and the photo folder on disk. The dashboard's "Removed" tab already existed as a label change; the backend just had to stop destroying the data.

**How to apply**: Any time a sync process detects "missing on source" and the local copy has historical value (price trajectories, photos, edit history), **never destroy — flag**. Add the dated `*_at` column instead of `DELETE`. Even if 100% of "missing" eventually turn out to be genuinely-gone, the audit trail is worth the disk. Bonus: a hot-backup before any destructive op (`scripts/backup_db.py` runs at `pipeline.py --mode full` start, keeps last 14).

---

## 2026-05-19 — Catch-all `listing_field_history` table (vs adding more dedicated per-field tables)

**Decision**: Added one generic `listing_field_history(listing_id, field, old_value, new_value, recorded_at)` table that captures any of 33 scalar field changes (title, status, year, color, transmission, seller_*, location, registration, ...) instead of adding 33 separate `*_history` tables. Kept the existing dedicated `price_history` / `mileage_history` / `description_history` tables for backward compatibility and because they store full snapshots (needed for ML).

**Why**: The user's request was "history for every change". Adding a new table per field is N×schema migrations and N×insert helpers. A generic key-value table covers the entire field surface with one row format, one helper (`_record_field_change`), and one query pattern. The dedicated tables earn their keep because price/mileage/description are scalar-aggregated heavily downstream (ML features, sparklines) and a full-value snapshot is faster than reconstructing from `new_value` strings. Photos got their own `photo_history` because the diff event (added/removed/replaced) doesn't fit a single old/new column.

**How to apply**: When the user wants "track everything" history and most fields are scalar, prefer one generic audit table. Carve out dedicated tables only for fields with heavy downstream consumers or non-scalar payloads.

---

## 2026-05-19 — `lxml` parser + `asyncio.to_thread` around `parse_listing`

**Decision**: BS4 instantiation switched from `BeautifulSoup(html, "html.parser")` to `BeautifulSoup(html, _BS4_PARSER)` with `_BS4_PARSER = "lxml"` if importable else `"html.parser"`. Pinned `lxml>=5.0` in requirements. In `pipeline.py:scrape_one`, the parse call is now `await asyncio.to_thread(parse_listing, html, listing_id, url)`.

**Why**: BS4 parse on a Skoda Superb detail page dropped 150 ms → 40 ms with lxml (≈4× faster). On the 88k full-refresh path that's hours saved. `asyncio.to_thread` doesn't parallelize parsing across the 500-per-chunk workers (default thread pool is small) — but it does prevent one worker's parse from blocking other workers' HTTP I/O on the event loop. Photos already had this treatment for Pillow encoding (decisions log 2026-05-18); applying the same pattern to BS4 is consistent.

**How to apply**: Default to lxml for any new BeautifulSoup usage; the only reason not to is a deployment that can't compile lxml's C extension. Any `await`-heavy worker that calls a CPU-bound library (BS4, lxml, Pillow, json with deep dicts, sklearn) inside an async function should wrap it in `asyncio.to_thread` — even single-worker code, because it keeps the event loop responsive for cancellation and other coroutines.

---

## 2026-05-19 — Optional features stored as many-to-many catalog match (not free-form text)

**Decision**: New `listing_features(listing_id, feature, section)` table with composite primary key. Parser collects all short text fragments from the detail page and matches against a hard-coded `FEATURES_CATALOG: dict[str, section]` (49 entries: Securitate + Confort sections, from the post-ad form). Unicode-normalised matching (`unicodedata.normalize("NFC", s).casefold()`) so 999.md's occasional ş/ș and ţ/ț cedilla/comma drift doesn't miss matches.

**Why**: Free-form text storage would mean later filter queries on "ABS" have to handle every spelling variant the site has ever shown. A canonical catalog also lets the user pivot the dashboard on features (e.g. "% of cars with panoramic roof" is a clean COUNT). The catalog can grow as 999.md adds form fields — unknown labels seen during scraping just don't get stored (logged for review). Defensive: collecting "all short text" + filtering by catalog membership is resilient to 999.md's class-name churn (no specific selector to break).

**How to apply**: For any scraper extracting a known-finite set of categorical tags from a third-party site, normalise + catalog-match rather than store raw. Match against `casefold + NFC + collapsed-whitespace` to absorb the kind of micro-formatting drift that breaks exact equality.

---

## 2026-05-19 — Pre-computed `price_predictions` cache table (vs on-request sklearn inference)

**Decision**: After each ML retrain, `web/ml.py:_fill_price_predictions` predicts every active listing once and writes the result to `price_predictions(listing_id, predicted_eur, delta_pct, flag)`. `/api/listings` LEFT JOINs this table so each row carries its prediction and flag without invoking sklearn. The Browse tab's "Deals only" filter is `EXISTS (SELECT 1 FROM price_predictions WHERE flag='deal')`.

**Why**: Inference per request would re-run sklearn over 24 rows per page (cheap) — but joining at request time on 88k active listings for the `dealsOnly` filter, sort, or count would re-run inference over the whole set on every page load (5-15s with Ridge). Pre-computing once per 24h hits ~5s total and gives O(1) lookup. The model_version column lets you tell which inferences came from the current model vs a prior pickle. Predictions clamped to [€500, €500k] in the fill step so mileage-outlier listings (10M km typos) don't pollute the deals feed with €60M predicted values.

**How to apply**: When ML inference would otherwise run inside a hot path (every page load, every search), pre-compute and cache. Re-fill on a schedule tied to model retraining cadence. Index the cache table on whatever the filter selects (`flag` here, `delta_pct` for ordering).

---

## 2026-05-19 — ML training gated at 500 archived listings, in-process daemon thread for 24h retrain

**Decision**: `web/ml.py:train_all_if_ready()` returns `{trained: False, current: N, required: 500}` if `n < MIN_TRAINING_ROWS=500`. `start_background_trainer()` (called from FastAPI startup hook) spawns a daemon thread that calls `train_all_if_ready` immediately then sleeps 86400s between retrains. Pickled models + meta to `E:\DB\models\{fair_price,days_to_sell,meta}.pkl` for warm-start across restarts.

**Why**: At cold start the user had 0 archived listings (we'd just fixed the destructive delete bug). Training on noise produces a worse-than-useless predictor; gating + a frontend "collecting data — N/500" placeholder is honest about state. Daemon thread is simpler than APScheduler or cron — no extra process, sklearn training is in-process anyway, and the GIL is fine because the heavy work is in C extensions (sklearn, lxml, sqlite). Pickling meta separately means the API can report R²/MAE/version after a restart without retraining; the daemon refreshes in the background.

**How to apply**: For any analytics that depends on data accumulating over time, gate on a count threshold and make the UI's gated state actionable ("run X to accumulate Y"). Daemon-thread schedulers are fine when the work is in-process anyway; reserve APScheduler / cron for cross-process or cross-machine coordination.

---

## 2026-05-19 (late) — Fast-path in `update_listing` for unchanged refreshes

**Decision**: Before doing the 40-column UPDATE + feature DELETE/INSERT + history writes, `db.update_listing` now checks: did ANY scalar field change AND did the description hash change? If not, it does a one-line `UPDATE listings SET last_seen_at, last_fetched_at` and returns. Same fast-path in `_sync_features`: skip everything if `new_set == prev_set`.

**Why**: In `--refresh-known` mode, 95%+ of listings have nothing changed between sweeps. The old code paid the full cost regardless: 40-column UPDATE, 30-row feature DELETE + 30-row INSERT, photo diff, history checks. Each unchanged listing was ~20-30ms of DB work. With 88k listings that's 30+ minutes of pure waste per refresh. The fast-path costs nothing for the rare changed-listing case (the diff happens anyway).

**How to apply**: For any sync/refresh pipeline that touches many records, always cheap-detect the no-op case before writing. The diff is essentially free; the writes are not.

---

## 2026-05-19 (late) — `--fast` calibrated to 999.md's measured soft-throttle, not arbitrary numbers

**Decision**: `--fast` sets `CONCURRENT_REQUESTS=12`, `REQUEST_DELAY_MS=(50,150)`. Initial attempt was sem=16 then sem=24; both were worse than sem=12.

**Why**: Direct benchmark against 999.md detail pages — at sem=16 p50 response time was ~1,065ms; at sem=24 it jumped to ~12,795ms. 999.md doesn't return 429s; instead it intentionally slows responses when you push concurrency. The ceiling is around sem=12-16. Pushing harder makes everything slower, not faster. We discovered this only by measuring; the README's older "8 concurrent is polite" comment was actually closer to the optimum than the aggressive numbers I tried.

**How to apply**: Before tuning a scraper's concurrency, benchmark p50 response time vs. concurrency level. Sources often hide their rate limits as response-time penalties instead of explicit 429s. The sweet spot is just below where p50 latency starts climbing.

---

## 2026-05-19 (late) — Sharded scraping doesn't help against a per-IP-throttled source

**Decision**: `--shard N/M` is available but `--fast` (single process) is the recommended path. Documented this in the `--shard` help text.

**Why**: User ran 4 shards expecting ~4× speedup. Instead: total throughput stayed flat AND one shard got 429'd (the 4th process pushed past the IP threshold). Sharding splits the same throttled pipe N ways. Each shard also independently re-runs the full GraphQL discovery (1,130 pages × 4 = 4× the load). Manifest-sharing reduces the discovery duplication but doesn't help the underlying throttle.

**How to apply**: Sharding only helps when the bottleneck is local (CPU, disk, single-process concurrency cap). For source-server-throttled workloads, optimize the single process instead: connection limits, polite delay, request shape, fewer round trips. Run multiple processes only if you have multiple IPs or auth tokens to use.

---

## 2026-05-19 (late) — HTTP/1.1 with many connections beats HTTP/2 multiplexing for the photo CDN

**Decision**: Switched `httpx.AsyncClient(http2=True)` → `http2=False` for the Session class.

**Why**: User's log showed repeated `StreamReset stream_id:N error_code:1 remote_reset:True` from i.simpalsmedia.com (the photo CDN) once we pushed CDN concurrency past ~40. HTTP/2 multiplexes all streams over a single TCP connection — the CDN's h2 implementation appears to reset streams beyond its per-connection limit. HTTP/1.1 opens many TCP connections (one per worker) which is more resource-intensive client-side but the CDN handles it fine. Net effect: same throughput, no errors, no wasted retry backoff (each StreamReset retry burned up to 24s of exponential wait).

**How to apply**: For CDNs and image hosts, prefer HTTP/1.1 with high connection-pool limits over HTTP/2 with high stream concurrency. HTTP/2 is great when the server has a generous stream limit; many real-world servers don't.

---

## 2026-05-19 (late) — Reading config from default-arg values in async classes is unsafe

**Decision**: `Session.__init__` no longer reads `config.CONCURRENT_REQUESTS` as a default argument value. It reads it from the `config` module inside the method body.

**Why**: Python evaluates default argument values at function-definition time (i.e. when the `class Session` block executes during import). Any later code that mutates `config.CONCURRENT_REQUESTS = 16` (like `--fast` does inside `pipeline.run()`) has NO effect on subsequent `Session()` calls — they still see the import-time value. This silently broke `--fast` for an entire user session. The user's first complaint that "it's not fast at all" was downstream of this bug.

**How to apply**: When a runtime-mutable config value is needed at object construction time, read it inside `__init__`, not as a default arg. This applies broadly to any "config-aware" classes in pipelines that get tuned by CLI flags.

---

## 2026-05-19 (late) — Junk inputs to ML training are a worse problem than small sample size

**Decision**: Training data + prediction cache both filter `year IS NOT NULL AND year BETWEEN 1980-2030 AND mileage_km BETWEEN 1000-500000 AND price_eur BETWEEN 500-200000`. Prediction-flag bounds tightened to `delta_pct > -90 AND < 500` so listings hitting model clamps don't appear as "deals".

**Why**: First version of the model trained on 407 archived listings, R²=0.859. Looked fine. But the top 5 listed "deals" were all seller typos: Mitsubishi with `10,000,000 km`, Dacia with `65,632,563 km`, Mercedes with `€1,111,111`. The model's prediction for those hit the upper clamp (€488,941) so they showed as -100% "deals". The user immediately noticed: "where did you take these prices?" The model wasn't lying — it was correctly extrapolating from garbage inputs. **A small clean dataset always beats a large dirty one**: after filtering, training shrunk slightly (407 → 406 valid) but R² IMPROVED to 0.873 and MAE dropped from €2,554 → €2,193. The deal feed became signal instead of noise.

**How to apply**: Aggressively filter outliers and structurally-invalid records (null required fields, impossible ranges) at BOTH the training step AND the inference/scoring step. The same row that would distort training would also produce a misleading prediction at inference time. Reject it at both ends.

---

## 2026-05-19 (late) — CSS Grid `grid-column: 1/-1` on hidden siblings doesn't free the column

**Decision**: `.layout` has `grid-template-columns: 260px 1fr`. On non-Browse tabs, `body[data-tab="dashboard|analysis|favorites"] .layout` collapses to `1fr`. Also pinned `.filters{grid-column:1}; .results{grid-column:2}` so the views never auto-flow into the wrong column.

**Why**: When `#filters` was `display:none`, the 260px column stayed reserved (CSS Grid keeps tracks even with hidden items). Worse, the four `.results` siblings auto-flowed: `#browseView` filled col 2 row 1, then `#dashboardView` got placed in col 1 row 2 (the 260px column), so it rendered at 260px wide on the wrong side of the page. Symptom matched the user's exact complaint: "cards on the left, growing." Two fixes were needed — explicit `grid-column` pinning AND collapsing the unused track entirely when the sidebar isn't there.

**How to apply**: When a layout has hidable sidebars, always either (a) pin grid items to specific columns AND collapse unused tracks via media-query or data-attr, OR (b) toggle the parent's `grid-template-columns` via JS state. Auto-placement in CSS Grid behaves surprisingly when items are conditionally hidden.

---

## 2026-05-19 (late) — `--refresh-older-than HOURS` is the practical alternative to smart-refresh

**Decision**: Added `--refresh-older-than HOURS` flag. Refreshes only listings with `last_fetched_at` older than the cutoff. Default operating pattern: one full sweep weekly, `--refresh-older-than 24 --fast` nightly.

**Why**: True smart-refresh would diff GraphQL summaries against the DB and only re-fetch changed listings. Introspection confirmed 999.md exposes the necessary fields (`reseted`, `posted`, `expire`) but they're empty for anonymous callers; `getAdsByIds` returns `UNAUTHENTICATED`. Without auth, smart-refresh is dead. The age-based fallback is honest about what we can actually do: spread refresh load over time. In steady state, only a few thousand listings are stale per night → ~15 min instead of 4.5h.

**How to apply**: When a "skip unchanged" signal is unavailable, fall back to "process by staleness" — process oldest-touched first, cap by count or by age. Same overall coverage spread over time.

---

## 2026-05-21 — Treat parse-stub on refresh as deletion, not an update

**Decision**: `pipeline.py` worker checks `_is_stub(data)` (no `make` AND no price in any currency). On a refresh path, stub → soft-archive via `scripts.verify_sold.delete_listing` (status='removed'), `listings_removed += 1`, no UPDATE issued. On a NEW path, stub → `errors += 1`, no insert. The `?` placeholders are gone from the log line — only fields that exist are printed.

**Why**: A "valid" refresh that came back with make/year/price all `NULL` was overwriting real DB rows with `NULL`s and leaving them `active` — silent data loss. Diagnosed when user spotted `upd 104380041 ? ?y ?€ (0 photos)`. The 999.md "Anunțul nu a fost găsit" page parses to exactly this shape, so it's almost always a listing that was deleted between discovery and the detail-fetch later in the run. Treating it as deletion preserves all prior data via the existing soft-archive path (status='removed' + removed_at, photos & history kept).

**How to apply**: When a parser returns a row of `None`s on what was supposed to be a known entity, the page probably isn't the entity anymore. Don't UPDATE with the empty row — branch into the "deleted" path (or at least skip the write). For any scraper of mutable third-party data: define an explicit "stub-shape" predicate per source, route stubs away from the normal write path. See [[999-carscrapper-deleted-while-running]] in mistakes.

---

## 2026-05-21 — `fast=True` is the default for `pipeline.run()`; CLI exposes `--no-fast`

**Decision**: Default-arg flipped on `pipeline.run()` from `fast=False` to `fast=True`. `--fast` becomes a no-op (default ON); `--no-fast` is the opt-out for polite/slow runs.

**Why**: Scheduler_f passes `fast=True` to every job. Operators running `python pipeline.py --mode full` from the shell had the slow path (sem=8, delay 200-600 ms) by default and assumed full mode was inherently slower than tick — it wasn't, the flag was just opt-in. The fast tunables (sem=12, delay 50-150 ms, cdn=32) are already calibrated to 999.md's per-IP throttle (sem≥16 → server slows responses; see decision above).

**How to apply**: When most callers pass the same non-default value, flip the default. Keep an opt-out flag rather than ripping the slow path out — it's still useful for one-off polite runs.

---

## 2026-05-21 — `tick` mode runs verify-missing too

**Decision**: The condition `if mode == "full":` that gates the verify-missing block in `pipeline.py` is now `if mode in ("full", "tick"):`. Scheduler_f's `tick` (every 10 min) now archives deleted listings instead of waiting for the Sunday `full`.

**Why**: Tick already does a full GraphQL discovery sweep (`max_pages=None` when called via scheduler_f), so `known_active - crawled_ids` is meaningful every 10 min. Per-IP verify cost is tiny (handful of listings disappear between ticks), and the 50%-discovery safety guard still kicks in if discovery looks partial. Net effect: removed listings now show as 'removed' in the UI within minutes instead of up to 7 days.

**How to apply**: Cheap-when-incremental work (small diff against a small window) belongs in the frequent job, not the weekly one — as long as a safety guard prevents catastrophic mass-archiving from a broken discovery pass.

---

## 2026-05-21 (web) — Three independent cache-bust mechanisms for the SPA assets

**Decision**: Frontend cache prevention is layered:
1. `index()` route injects `?v=<mtime>` into the `/static/app.js` and `/static/style.css` URLs based on file modification time.
2. `index()` response sends `Cache-Control: no-cache, no-store, must-revalidate` on the HTML.
3. `NoCacheStaticFiles(StaticFiles)` subclass sends the same headers on every JS/CSS response.

**Why**: A single layer wasn't enough in practice. Versioned URLs alone failed because the BROWSER held the old HTML (with the old `?v=` tags) in its cache. HTML no-cache alone wasn't enough because Chrome's disk cache for the static files persisted across reloads on localhost even in incognito. Adding all three guarantees fresh fetches on every reload, no matter how aggressive the browser cache is. Bandwidth cost on a single-user dev tool is negligible; debugging-frustration cost of stuck cache is huge.

**How to apply**: For single-user dev sites, prefer `no-cache` everywhere over relying on ETag/Last-Modified. For multi-user production, drop point 3 (keep version-busting + HTML no-cache) so static assets can still be CDN-cached.

---

## 2026-05-21 (web) — Portrait-photo fit: flex centering + max-constraints, not grid + 100%-dimensions

**Decision**: `.detail-photos .main-photo` is now `display: flex; align-items: center; justify-content: center` with the img using `max-width: 100%; max-height: 100%; width: auto; height: auto`. Previously was `display: grid; place-items: center` with img `width: 100%; height: 100%; object-fit: contain`.

**Why**: The old grid+100%-dimensions setup had a circular sizing dependency: the img's `height: 100%` resolved against the grid row's height, but the grid row's height was sized to fit the img's natural aspect ratio. For a 432×960 portrait, the row inflated to 1414px tall inside a modal capped at 92vh (~993px), and `overflow: hidden` on the card just clipped the bottom — the photo appeared cropped with the car cut off. Flex centering + `width: auto / max-*: 100%` lets the browser size the img to its natural aspect, bounded by parent — portraits letterbox horizontally, landscapes letterbox vertically.

**How to apply**: Don't combine `width: 100%; height: 100%` on an img with a parent that doesn't have an explicit fixed height — the intrinsic-ratio resolution can blow out the parent. Use `max-width: 100%; max-height: 100%` + `width: auto; height: auto` when you want a "fits inside, preserves ratio" image. Reserve `object-fit: contain` for when you specifically want the IMG box to be the parent's exact size and the visible photo inside it letterboxed.

---

## 2026-05-21 — Capture USD prices natively (new column, not converted)

**Decision**: Schema gained `listings.price_usd`, `listings.old_price_usd`, `price_history.price_usd`. Parser regex extended to `(€|EUR|MDL|lei|leu|USD|\$)`. `_parse_prices()` returns a 4-tuple. `init_db()` runs additive `ALTER TABLE` migrations (wrapped in `try/except OperationalError`) so existing DBs upgrade in place. `currency_listed` now also takes `'USD'`.

**Why**: Some sellers (often imports / dealer cross-listings) price exclusively in USD. The old regex only matched `€/EUR/MDL/lei/leu`, so those listings had `price_eur=NULL, price_mdl=NULL` and were invisible to every price-based query (deals filter, ML training, analytics). Native column preserves fidelity — converting USD→EUR at parse time would bake in a fixed rate and corrupt historical comparisons when the rate drifts.

**How to apply**: When you discover a third currency / unit / category in source data, add a column, don't normalize at ingest. Conversion is a presentation concern; storage should be lossless. Additive `ALTER TABLE` + per-statement `try/except` is the cheap migration pattern for SQLite.

---

## 2026-05-22 — Relisted-car detection: link, don't merge (`car_identity` cluster)

**Decision**: Photo perceptual hashes (imagehash.phash, Hamming ≤ 6, ≥ 2-of-3 first photos must match) detect when a new listing is the same car the seller deleted and reposted. Instead of merging the new row into the old one, both rows stay intact and link to a shared `car_identity` cluster row (`current_listing_id` points at the newest, `listing_count` increments, `status` stays `'active'` while ANY member is active). The new listing also stores `relisted_from_listing_id` pointing back. The cluster only flips to `removed` once every member is soft-archived.

**Why**: option (a) "merge new into old" destroys real history — price changes, mileage edits, photo swaps between reincarnations. It also collapses the rare "dealer has two genuinely identical cars" case. Option (c) "just-flag with a boolean" loses the cross-listing timeline. Linking with a cluster (option b) preserves every delta, surfaces the dealer tactic in the UI ("🔁 Relisted 3× — same car first seen 2025-09-14, 187 days on market"), and lets the ML model use cluster lifetime as a feature instead of being fooled by a fresh listing date.

**How to apply**: Whenever you'd be tempted to dedupe records into one canonical row, prefer the "many rows + one cluster row" pattern. It costs one INTEGER FK on the source table and one cluster table; it preserves audit history, supports cross-cluster analytics (count, time-spans), and gives you a non-destructive escape hatch ("just unlink") if the matcher is wrong.

---

## 2026-05-22 — pHash stored as SIGNED 64-bit; XOR for Hamming

**Decision**: `imagehash.phash` returns a 64-bit unsigned hash but SQLite INTEGER is signed 64-bit. Both `scraper/photo.py:_phash64` and `scripts/backfill_phash.py:_phash_for` wrap the value into the signed range (`if u >= 2**63: u -= 2**64`) before writing. The Hamming-distance helper uses `bin((a ^ b) & ((1 << 64) - 1)).count("1")` so XOR is masked back to 64 bits.

**Why**: storing the raw unsigned value triggers `OverflowError: Python int too large to convert to SQLite INTEGER` on inserts above 2^63-1 (about half of all phash values). Casting to TEXT would work but kills the natural integer comparison + lets us use a B-tree index. Signed wrap keeps the bit pattern identical — XOR is unaffected.

**How to apply**: SQLite INTEGER ≤ 2^63-1. Any time you store a hash, ID, or epoch nanosecond that's nominally u64, wrap to signed at the boundary. The XOR/AND/OR bitwise operations are bit-identical between signed and unsigned representations, so Hamming/equality checks need no other change.

---

## 2026-05-22 — Removed-tab pagination: status filter must flip `has_user_filters`

**Decision**: `web/queries.py:build_listing_query` sets `has_user_filters = True` not only on equality/range/multi-select filters but also when `status != "active"`. The web app uses that flag to decide whether to run a real `COUNT(*)` for pagination or reuse the cached active-count.

**Why**: the previous code only flipped the flag for sidebar filters; the status toggle was treated as a no-op. Pagination kept using the cached "89,773 active" count even when the user switched to Removed (which has ~6,861 rows). UI rendered 3,400+ ghost pages, most empty. Counts now match the actual filtered set.

**How to apply**: any flag that gates "is this a default query / can we use a cached count" must be flipped by EVERY narrowing filter, including ones that look like simple state toggles. A useful test: would the COUNT change between the toggle's positions? If yes, the toggle is a filter.

---

## 2026-05-22 — `init_db()` runs additive `ALTER TABLE` BEFORE `executescript`

**Decision**: `db.init_db` does the `ALTER TABLE ... ADD COLUMN` migrations FIRST, then runs `executescript(schema.sql)`. Both blocks are wrapped to ignore failures: ALTERs fail silently on fresh DBs (parent table doesn't exist yet), and `CREATE IF NOT EXISTS` is a no-op on existing tables.

**Why**: schema.sql now contains `CREATE INDEX IF NOT EXISTS idx_photos_phash ON photos(phash)`. On an existing DB that pre-dates the phash column, executescript hits the index DDL before the migration adds the column → `OperationalError: no such column: phash` aborts the whole script. Reversing the order lets the migration add the column first, then the index DDL runs cleanly. On fresh DBs the ALTERs silently fail (no parent table), executescript creates everything from the canonical schema, no harm done.

**How to apply**: when adding a column AND an index on that column in the same migration, always run the column-add (ALTER) before the index-create (executescript). The pattern generalises: indexes/triggers/views in schema.sql will fail if they reference columns the existing DB doesn't have yet. Migrate first, then schema.

---

## 2026-05-22 — `build_extra_filters(params, alias)` for shared filter SQL

**Decision**: `web/analytics.py` exposes `build_extra_filters(params, alias="")` that returns `(" AND col1=? AND col2 IN (...)", [args])` from the same query-param shape `web/queries.py` parses for `/api/listings`. The optional `alias` arg prefixes column names with `<alias>.` so the same fragment can be appended to a query that has the `listings` table aliased.

**Why**: the model-stats endpoint needs to filter every sub-count (active, sold_total, sold_recent, median_sold, avg_days, sold_by_year) by the same sidebar filters the user has applied in Browse. Without a shared helper, every analytics function would either: re-implement the parsing (drift risk), or string-replace column names to add an alias prefix (brittle — caught me with a "year" → "l.year" replace that almost mangled "...year ..." substrings inside other patterns). The alias-aware helper is the clean version.

**How to apply**: when two queries against the same table need the same filter logic but one of them JOINs and aliases the table, build the filter helper with an alias parameter from the start. Don't string-replace SQL after the fact — too easy to break.

---

## 2026-05-22 — Cohort card uses tokens, not raw hex (root cause of broken chip render)

**Decision**: All `.model-stats-card` and `.ms-year-chip` CSS uses the project's existing semantic tokens (`--surface`, `--surface-2`, `--surface-3`, `--border`, `--text`, `--text-soft`, `--text-faint`, `--accent`, `--accent-soft`, `--accent-border`). The previous version referenced `--card`, `--divider`, `--bg-elevated` — none of which exist in this project. Fallback colors barely registered against the dark theme, so chip borders/backgrounds dissolved and year chips read as one run-on string.

**Why**: dark/light mode + state-consistent rendering depends on the theme system. Any component that defines its own raw hex colors will desync from the rest of the app the moment a token shifts (or worse, look broken in only one mode). Tokens also let the new cohort card automatically work in light mode without a second pass.

**How to apply**: before writing any new component CSS, grep the existing `style.css` for `--*` definitions. Never invent token names; use what's defined. If the design needs a token that doesn't exist, add it to `:root` (and the light/dark variants) first, then reference it.

---

## 2026-05-23 (later) — Relisted-car treatment everywhere: merge into active twin, exclude from Sold

**Decision**: A `car_identity` cluster with at least one `status='active'` sibling represents a car that's STILL FOR SALE — the seller just refreshed the post. The active sibling becomes the canonical view. Three downstream consequences:

1. **Detail modal** (`/api/listings/{id}`) merges `price_history` + `mileage_history` from every cluster sibling into one chronologically-sorted series, each point tagged with its originating `listing_id`. The frontend chart colors points by id so relisting boundaries are visible. Backend returns `cluster.first_seen_at_overall` (oldest sibling) + `cluster.listing_ids`; UI shows dual "first seen" tiles.
2. **Removed/Sold listings tab** (`web/queries.py`) — adds `NOT EXISTS (SELECT 1 FROM listings sib WHERE sib.car_identity_id = listings.car_identity_id AND sib.status='active')`. Removed-bucket listings whose physical car is now relisted-active disappear from the view.
3. **Model-stats counts** (`web/analytics.py`) — `sold_recent_truly` / `sold_total_truly` mirror the same exclusion. Headlines use truly-sold; raw counts stay so the info-tooltip can show "X listings were deleted, Y were relisted." Also flipped "Active" to `COUNT(DISTINCT COALESCE(car_identity_id, -id))` so the headline = unique cars; `active_total_listings` + `active_duplicates` power the info-tooltip.

**Why**: relisting is the dominant noise source in marketplace data. A dealer posting a `Lada BA3 2108` three times in two weeks should not (a) appear three times in stats, (b) get counted as two "sold" events, or (c) show a price-history reset every time the post id changes. The cluster grouping already exists from pHash matching (2026-05-22); we were just refusing to use it for anything except the relisted-banner UI. Cluster identity is now the unit of analysis for active inventory + sales counting; raw listings remain the unit for things that are inherently per-post (e.g. days-on-market for a single listing).

**How to apply**: any new query in `web/queries.py` or `web/analytics.py` that touches `status IN ('sold','removed')` or counts active inventory must decide: do I want raw listings or unique cars? For Sold/Removed, AND the `NOT EXISTS` cluster-has-active fragment. For unique active inventory, dedupe via `COUNT(DISTINCT COALESCE(car_identity_id, -id))`. The negated-id trick avoids collisions between standalone listings and positive cluster ids. **Sanity check after any model-stats change**: top-bar KPI `Active listings` and side-card `Active` must match — divergence means a buyer-side or cluster filter is missing somewhere.

---

## 2026-05-23 (later) — `_NOT_BUYER` must live in `web/analytics.py` too

**Decision**: `web/analytics.py` gets its own module-level `_NOT_BUYER = "(offer_type IS NULL OR offer_type != 'Cumpăr')"` and folds it into `REMOVED_FILTER` + every `active`/`sold_*` query. Until today only `web/app.py` carried the filter, so analytics endpoints were silently counting buyer-side listings.

**Why**: the top-bar KPI strip (from `/api/stats`) and the model-stats card (from `/api/analytics/model_stats`) showed mismatched active counts — 86,169 vs 89,635 — because the latter wasn't stripping `Cumpăr`. Two sources of truth, one of them inflated by 3,466 buyer-side ads. The fix isn't to import from `web/app.py` (circular) — it's a duplicate constant. Acceptable duplication for the price of zero coupling.

**How to apply**: any new file that runs SQL against `FROM listings` must filter `Cumpăr` — either via `_status_where` (if going through `app.py`) or by AND-ing `_NOT_BUYER` directly. New analytics endpoints: copy the filter pattern from the existing `active`/`sold_total` queries in `model_stats`.

---

## 2026-05-23 (later) — Price history is a Chart.js time-series, not a sparkline

**Decision**: The detail-modal price + mileage history widgets render via Chart.js with `type: 'time'` (X = `recorded_at`, Y = value, visible 4px points, hover tooltip with date + listing id). Required CDN add: `chartjs-adapter-date-fns@3.0.0`. The old inline-SVG `sparklineSVG()` helper stays in the codebase for any future thumbnail-sized use but is no longer wired into `renderDetail`.

**Why**: once histories are merged across cluster siblings, the series can span multiple months with non-uniform spacing — exactly what a time scale handles correctly and an evenly-indexed sparkline fakes. More importantly, points need identity (which listing each came from) so relisting boundaries are visible; SVG had no tooltip infra. Cost: ~30KB extra JS (Chart.js already loaded for dashboard; adapter is the only new payload).

**How to apply**: `renderHistoryChart(canvasId, points, getValue, unit, thisListingId)` in `web/static/app.js`. Points whose `listing_id` differs from `thisListingId` render in `#94a3b8` (dim grey) instead of `--accent` so the visual reads "this listing in color, prior listings ghosted." Don't set `parsing: false` — the time scale uses the adapter to parse ISO strings during data ingest; turning off parsing skips the adapter and the chart blanks.

---

## 2026-05-23 (later) — Sell-through rate uses cohort-in-window denominator, not lifetime listings

**Decision**: The new "Sell-through" tile in the model-stats card computes `truly_sold_in_window / (active + truly_sold_in_window) × 100`. Numerator is the relisting-deduped sold count (`sold_recent_truly`). Denominator is "cars that touched the market in this window" — currently-active plus truly-sold. Computed in `web/static/app.js:renderModelStatsCard()`, no backend change.

**Why**: three other formulas were on the table and rejected:
- `sold / total_listings_ever_in_cohort` — drifts to ~0 over time as historical inventory accumulates faster than current sales. Useless for trend reading.
- `sold / active` — can exceed 100% trivially (more sold this quarter than currently listed) and the value has no intuitive ceiling. Confusing.
- `sold_listings (raw) / (active_listings + sold_listings)` — counts relistings of the same physical car in both the numerator and denominator, double-deflating slow-moving segments. Fix: use the truly-sold count, which is already cluster-deduped.

The chosen formula has a clean ceiling at 100% (everything in the window sold), a clean floor at 0% (nothing moved), and reads intuitively as "of the cars that were in front of buyers this window, what fraction left via sale."

**How to apply**: any future "rate" metric over a window should compute as `event_count / (still_open + event_count)`, where `still_open` is currently-active and `event_count` uses the cluster-deduped variant for events that can repeat per physical car. Always client-side when the inputs are already in the same payload — server-side computation just adds a field for no gain. Display tiers: `≥10%` → integer, `1–10%` → one decimal, `>0 <1%` → render `<1%` literally (a real-but-tiny rate must never display as 0% or users will believe nothing sold).

---

## 2026-05-23 (later) — Scrollbars themed via `var(--border-strong)` not hex

**Decision**: All `::-webkit-scrollbar-*` rules reference theme tokens (`--border-strong` for thumb, transparent track, `--text-faint` on hover). Firefox uses the `scrollbar-color: var(--border-strong) transparent` shorthand on `html`. Slim 8px variant scoped to `.detail-card`, `.filters`, `.thumbs` (the three high-contrast bars the user flagged).

**Why**: default Windows chrome was bright white against `#161618` panels and yelled louder than the content. Hex-coded scrollbars would have desynced from light mode. Using `--border-strong` automatically re-tones because both themes define it.

**How to apply**: when adding a scrollable region that needs a slimmer bar, append the selector to the existing `.detail-card, .filters, .thumbs` rule rather than creating a one-off override. Never hex-code scrollbar colors in this project.

---

## 2026-05-26 — KPI strip auto-refreshes every 30s with slide-up animation on value changes

**Decision**: `renderKpis()` in `web/static/app.js` now sets a 30s `setInterval` that re-fetches `/api/stats` + `/api/analytics/kpis`. A `_kpiPrev` map tracks the last-displayed value per tile. When a value changes, the number is wrapped in `<span class="kpi-num slide-up">` which plays a 450ms CSS `translateY(100%→0)` animation. First paint is instant (no animation). Unchanged values are left untouched.

**Why**: The user wanted the top-bar stats to feel "live" without manual refresh. 30s poll interval is compatible with the server's 60s TTL cache — values update roughly every minute with visible motion highlighting what changed. The slide-up direction (bottom → top) matches the mental model of "new data arriving".

**How to apply**: For any dashboard KPI strip that should feel live, poll on a schedule slightly under the server cache TTL and animate only changed values. Don't animate on first paint — it's disorienting with no prior state to compare against.

---

## 2026-05-26 — "Hide ordered" filter uses structured `availability` + `offer_type` fields, not description parsing

**Decision**: New "Hide ordered" checkbox in the Browse toolbar. When active, `web/queries.py` adds `(availability IS NULL OR availability != 'La comandă') AND (offer_type IS NULL OR offer_type != 'Auto la comandă')`. Same logic in `web/analytics.py:build_extra_filters` so the model-stats side-card respects the toggle. No description text parsing.

**Why**: ~7,659 listings have `availability = 'La comandă'` and ~4,176 have `offer_type = 'Auto la comandă'` — these are structured fields set by the seller via 999.md's post form, not free text. Description parsing would produce false positives: a car with "interior la comandă" (custom interior) would get wrongly excluded. The structured fields are authoritative for "this car is not in stock, it's imported on order" and have zero overlap with custom-feature descriptions.

**How to apply**: When filtering a marketplace category that has a structured metadata field, always prefer that field over description text mining. Text mining is a last resort for signals that only exist in free text. For any new filter toggle, wire it through BOTH `web/queries.py:build_listing_query` (for the grid) AND `web/analytics.py:build_extra_filters` (for the side-card stats) to keep them in sync.

---

## 2026-05-27 — Sell-through tab: year buckets over generation text, top 40 makes, no user filters

**Decision**: New "Sell-through" tab ranks every (make, model, year_bucket, fuel, mileage_bucket) combo by sell-through %. Year buckets are fixed 5-year windows (…, 2014-2018, 2019-2023, 2024+). Mileage is two categories (0-100k, 100k+). Only the top 40 makes by listing volume appear. The page has no sidebar filters — just a time-window toggle (30/60/90/180d) and client-side year-chip filter. All columns are sortable.

**Why**: Three failed approaches led here:
1. **Generation text grouping** — the `generation` column from 999.md is free-text ("V (2016 - prezent)", "F30", or NULL). NULLs created tiny orphan buckets that showed 100% sell-through with 0 active / 7 sold — technically correct but useless. Different text variants for the same year range split real cohorts.
2. **Body type as a grouping dimension** — splitting by body type fragmented data further. A Daihatsu Cuore with 3 active / 13 sold in Browse showed as 1 active / 10 sold on the sell-through page because only the Sedan rows were in one bucket. Removing body_type collapsed the fragments.
3. **Full dedup mismatch** — the sell-through query initially used `_cluster_dedup_sql()` (cluster only) while Browse's model_stats used `_dedup_sql()` (relisting + cluster). Numbers diverged. Switched sell-through to match model_stats exactly. Active listings also get cluster-deduped via NOT EXISTS to match Browse's unique-car count.

**How to apply**: when building a cross-cutting ranking that users will cross-reference with per-cohort stats on another page, use **identical dedup logic** and group only by dimensions that don't fragment below the minimum-sample threshold. Year buckets are stable (every listing has a year); generation text is not.

---

[[../projects/999-CarScrapper|← Back to 999 CarScrapper wiki]] · [[../decisions|← Global Decisions]]
