# 999-CarScrapper — Chat History

> Log of important Claude Code sessions for this project.

---

## Sessions

### [2026-06-04] Relist false-positives — pHash collides on showroom photos; whole identity model rethought

**What was asked**: "let's think how we can solve the problem with relists on the 999 auto scrapper" → audit the live clustering, find the wrong merges, then design a better algorithm and dry-run it on 30k cars.

**Audit**: sampled 1,000 multi-member clusters, montaged + eyeballed. Found systematic **dealer-fleet false merges** (Mercedes E-Class spanning years 2011/13/16, Tucson mixing 2 body generations, Ford Focus/Auris tied by "X auto"/"BROAUTO" banners). Data floor: 93/1,000 had a physically-impossible conflict (year-span ≥3 or mileage drop >30k) ⇒ ~1,500 definitely-wrong clusters. Gave the user a ranked list of the 100 worst; they confirmed.

**Pivots driven by the user**:
1. **SM6 reclassified as a REAL relist** — same car cross-posted in two cities. ⇒ killed my attribute-veto design (city/seller/price/small-mileage are NOT vetoes). See [[../mistakes#2026-06-04 — Built attribute *vetoes*]].
2. The "ad" to strip is a **whole image that's just the dealer advert**, identical across all that dealer's listings → detect by recurrence.
3. **Blurred-plate** cases: a real relist whose plate was blurred drifts the pHash and changes the description → "exact 1:1" misses it.
4. A sub-agent confirmed **`mileage=1` is a placeholder** on 2,873 listings (`2025+1km` = 1,163 cars) — mileage can only corroborate, and only when rare.

**The decisive finding** (via `scripts/relist_v2.py` on a 30k batch): the new "exact-photo" algo *still* built an 85-car Peugeot 3008 chimera. Root cause proven — two different-mileage 3008s share **3 byte-identical 64-bit pHashes** (each shared by 8 cars), photos visually identical (same AUTOPLAZA.MD showroom). **pHash measures composition, not identity.** See [[../mistakes#2026-06-04 — Trusted 64-bit pHash]].

**Outcome**: derived a new model — gate (make+model+year±1+fuel) + **two-tier evidence** (rare-photo OR common-photo+rare-metadata) + **clique** (no transitive chaining) + **ORB** verify for blurred plates. Unifying law: *every signal must pass a rarity gate.* **Nothing shipped to live clustering** — `db/database.py` unchanged; an ID-search web feature was added then reverted by the user. Full write-up: [[../999-CarScrapper-relist-identity-rethink]].

**Files**: `scripts/relist_v2.py` (new, read-only dry-run; outputs to `E:\DB\audit\relists_v2\`). `scripts/audit_relists.py` + `scripts/list_wrong_relists.py` were created then removed by the user. Vault: new deep-dive page + decisions + mistakes (×2) + todo.

---

### [2026-06-02] "These two cars are the same listing" — dealer relists missed by the pHash matcher

**What was asked**: user screenshotted two grid cards of the same Hyundai Tucson 2022 (interauto.md), one removed 05-28, one removed 06-02, same price/photos — "find out what caused the error and fix it for all the other listings."

**Diagnosis** (data-driven, not guessed): pulled both listings' photo phashes from the DB and computed cross-Hamming. The matching front-3/4 photo scored **10** bits (same image, CDN-re-encoded on repost); several other photos were exact 0s but sat at idx 6/12/18/19. The matcher used Hamming **≤6** over only the **first 3** photos — and slot 2 was the dealer's promo banner (correctly excluded as a template), leaving 2 re-encode-drifted photos that both blew past 6 → 0 matches → two singleton clusters (82494, 91250) instead of one.

**Two root causes**: (1) threshold too strict for CDN re-encodes; (2) scan window too narrow once a template-banner + gallery reorder are in play.

**Fix**: `db/database.py` — `PHASH_HAMMING_THRESHOLD 6→10`, `PHASH_MATCH_FIRST_N 3→8` (req stays 2). Validated thr choice on **741 distinct-car Tucson pairs**: thr=10 → 0 FP, thr=12 → 1 FP. Then wrote **`scripts/merge_relists.py`** (new) — non-destructive, resumable, lock-tolerant; revisits only singleton clusters and merges genuine relists via the live logic — chosen over `reset_clusters`+rebuild because the scheduler/refresher/web were live and 15k good clusters shouldn't be churned.

**Verification**: backed up first (`listings-20260602-201523.db`). Tucson scoped apply: 61 merges (target pair unified, count=2, orphan deleted). Global apply: **2,748 merges**, and a backup-vs-current diff proved **0 new chimeras**, count-mismatches *down* (17,209→16,709), orphans/mismatches confirmed pre-existing (not introduced).

**Flagged to user**: must **restart `scheduler_f.py` + `refresher_loop.py`** (they cache old constants); and a separate pre-existing cluster-bookkeeping debt (~5k orphans, ~16.7k stale counts) worth a future `reconcile_all_clusters` sweep.

**Files**: `db/database.py` (constants + comments), `scripts/merge_relists.py` (new). Vault: [[../999-CarScrapper-relist-phash-tuning]] (deep-dive), [[../999-CarScrapper-dedup-consistency]] (params updated), decisions, todo.

---

### [2026-05-30] Scheduler "acting up again at 300 listings" — burst resilience + a self-inflicted timeout bug

**What was asked**: "the scheduler is acting up again at only 300 listings, just fix it so it won't trouble if I run it at the start of the day and there'll be a bit too many listings once."

**Misread #1 (mine)**: First diagnosed it as the documented 480s tick-timeout budget problem (sequential discovery eating ~4 min). I parallelised discovery + raised the timeout. Useful, but not the symptom the user saw.

**The user corrected me**: the real symptom was `(0 photos)` on a handful of listings, then a ~5-min freeze, then "tick done". Re-reading: some `(0 photos)` are *correct* (`Cumpăr` buyer posts skip photos by design); the freeze is the throttle→ban→`getaddrinfo`-starvation cascade from the rate-limit runbook. To make the tick **survive** that without freezing, I added a per-listing `asyncio.wait_for` timeout + a consecutive-failure circuit breaker.

**Then the breaker fired falsely** — and the log exposed a bug in *my own* timeout. 113 listings succeeded with photos (~1s each, 999.md totally fine), then **all 308 remaining timed out at the same instant** and tripped the breaker with a misleading "likely banned" message. Cause: `asyncio.gather` starts all 421 coroutines at once, so every `wait_for(120s)` clock started at T0, but only 12 can fetch (site semaphore). Listings queued deep burned their whole 120s *waiting in line*, never fetching → mass timeout at T0+120s. The timeout measured "time since the batch started", not "time since this listing started fetching". (Tell-tale: all 308 share one timestamp.)

**Final fix**: a `launch_gate` semaphore (`2 × CONCURRENT_REQUESTS`) the worker must acquire **before** the timeout clock starts — so the clock measures fetch time, not queue time. Sized above the fetch sem so detail+photo phases overlap (no throughput loss). Reproduced the bug and confirmed the fix with a 60-task/sem-6 sim (no-gate: 12 of 60 wrongly timed out; gated: all 60 finish). User confirmed: "its working".

**Behaviour after fix**: a 421-listing burst now drains fully in one tick (~40–50s processing at 12-wide) instead of stopping at 113. The 113 already inserted that run are safe (commit-per-listing); the 308 skipped reappear as `new` next tick. Root cause of the *throttling itself* (scheduler 12 + refresher 12 = 24, over the ~16 line) is unchanged and was left alone per the user's earlier "keep the refresher continuous" call — these changes make the tick degrade gracefully, not reduce volume.

**Files changed**: `scraper/crawler.py` (`_discover_parallel` + `discover_all` dispatch), `config.py` (`DISCOVERY_CONCURRENCY`, `PER_LISTING_TIMEOUT_S`, `ABORT_AFTER_CONSEC_FAILURES`), `pipeline.py` (worker returns bool, `_bounded` + `launch_gate` + circuit breaker), `scheduler_f.py` (tick timeout 8→15 min). Vault: [[../mistakes#2026-05-30 — A per-task asyncio.wait_for timeout over a semaphore-gated gather]], [[../999-CarScrapper-ratelimit-throttle-dns]], todo.

---

### [2026-05-28 later] Two follow-on bugs surfaced once both processes ran

**Bug 1 — Refresher was inserting new listings too, racing the scheduler**.
User noticed `NEW <id>` lines in the refresher log. Root cause: I had reverted
the `skip_discovery` flag the user initially rejected, so the refresher also ran
`discover_all` + diff + `insert_listing`. Both processes called
`INSERT OR REPLACE INTO listings` for the same new IDs; whichever wrote second
CASCADE-deleted the first's photos + history rows (every child table has
`ON DELETE CASCADE`). Silent data loss.

Restored `skip_discovery=True` + `skip_backup=True` on the refresher's
`run()` call. Refresher now pulls active IDs straight from the DB, skips
discovery / verify-sold / new-id insert entirely. Refresher log should show
only `upd` lines, never `NEW`, and `pages_crawled: 0` in stats.

**Bug 2 — `database is locked` on scheduler tick**.
The per-chunk shared SQLite connection held the write transaction for the full
~17 min of a 2000-listing chunk. SQLite WAL allows many readers but only one
writer. Scheduler's `touch_seen` waited the 30 s connect timeout and died.

Fix: `conn.commit()` after every worker's write. Releases the write lock between
listings while keeping the connection reuse. Cost: one WAL fsync per listing
(~1–2 ms). Cheap vs the lockout it prevents.

**Lesson worth keeping**: when two long-running processes share a SQLite DB,
"shared connection per chunk" is the wrong granularity. Either commit per
operation OR drop the shared-conn optimization. The connect/close overhead
saving is real (~3–8 min on 89k listings) but holding a write transaction
that long starves any other writer.

**Files changed**: `pipeline.py` (re-added `skip_discovery` / `skip_backup`,
added per-listing `conn.commit()`), `refresher_loop.py` (passes both flags).

---

### [2026-05-28] Split scheduler + refresher into two processes, speed up refresh

**What was asked**: Make `pipeline.py --mode full --refresh-known` run faster, loop it continuously, and lock `scheduler_f.py` to new-listings detection only.

**Architecture decision**: Two processes run in parallel.
- `scheduler_f.py` — tick-only (every 10 min): GraphQL discovery + new-ID detail-fetch + verify-sold. Removed `incr` and `full` jobs.
- `refresher_loop.py` (new) — loops `run(mode="full", refresh_known=True, fast=True)` back-to-back with 30s pause + 6h per-pass timeout + signal-handled graceful shutdown.

Earlier attempt added `skip_discovery` / `skip_backup` flags to make the refresher cheap. User rejected — wanted it to behave identically to the standalone command, just faster. Reverted those flags.

**Speedups landed in `pipeline.py`**:
1. **One HTTP `Session` for the whole run** instead of one per chunk. Was re-warming TLS ~178 times per 89k pass.
2. **One SQLite connection per chunk** shared across all workers in that chunk. Was opening/closing ~89k connections per refresh pass. Safe because asyncio coroutines don't preempt and the DB op blocks have no `await`s.
3. **`SCRAPE_CHUNK_SIZE` 500 → 2000** in `config.py`. Fewer chunk boundaries.

**Why request concurrency wasn't touched**: code comments + prior calibration show sem=12 / cdn=32 are the empirical ceilings — pushing higher triggers 999.md soft-throttle (p50 1s → 13s at sem=24) and StreamReset on h2 at cdn>40.

**Expected impact on 89k refresh**: ~5–10 min saved per pass; network floor is still ~62 min at sem=12.

**Files changed**: `pipeline.py` (shared session + per-chunk conn), `config.py` (chunk size), `scheduler_f.py` (tick-only). **New**: `refresher_loop.py`.

**Coverage Q&A**: User asked if scheduler can miss listings. Answer: only if a listing is posted AND deleted entirely between two ticks (10-min window). Within a single tick, GraphQL paginates the entire feed and stub-detection soft-archives anything deleted mid-fetch.

---

### [2026-05-27] Sell-through tab + model_stats cluster dedup fix

**What was asked**: User wanted a new page showing top sell-through rates across all car segments, with year/fuel/mileage categories visible per row. Also noticed the Browse side-card stats didn't match the grid (14 sold shown in stats vs 4 listings visible).

**Root causes found**:
1. **model_stats `sold_total_truly` only applied relisting filter, not cluster dedup** — Browse grid applied both (via `queries.py`), creating a 14 vs 4 mismatch. Fixed by extracting `_dedup_sql()` as a reusable helper combining both filters.
2. **`_dedup_sql("")` generated ambiguous SQL** — unqualified `car_identity_id` inside NOT EXISTS resolved to the subquery's `sib` table, not the outer `listings`. Made every sold listing match the exclusion → 0 truly-sold results. Fixed by defaulting to `"listings."` prefix.
3. **Generation text grouping was misleading** — NULL-generation Honda Accords formed a 0-active/7-sold bucket showing 100% sell-through, while the real cohort had 54 active. Switched to `_year_bucket(year)` with fixed 5-year windows.
4. **Body type splitting fragmented data** — Daihatsu Cuore showed 1 active / 10 sold (Sedan only) instead of Browse's 3 active / 13 sold (all body types). Removed body_type from grouping.

**Files changed**: `web/analytics.py` (new `_cluster_dedup_sql()`, `_dedup_sql()`, `_year_bucket()`, `_mileage_bucket()`, `sell_through_segments()`; refactored `model_stats()`), `web/app.py` (new endpoint), `web/static/app.js` (new tab + rendering), `web/static/index.html` (tab button + view section), `web/static/style.css` (sell-through styles).

**Final state**: Sell-through tab shows ~2,800 combos ranked by ST%, top 40 makes, 5-year year buckets, 2 mileage categories, sortable columns, year chip filter. Honda Accord Hybrid 0-100k 2019-2023 shows 54 active / 11 sold / 16.9% — matches Browse (55 active / 11 sold / 17%).

**Also fixed**: `database is locked` crash on `pipeline.py --mode full --refresh-known`. Both `connect()` and `init_db()` in `db/database.py` had no `timeout` — SQLite gave up instantly when the web server's read-only WAL connection briefly blocked writes during checkpoint. Added `timeout=30` to both.

---

### [2026-05-24] pHash cluster matcher was producing chimeras — added template-phash exclusion + make+model gate
**What was asked**: After kicking off `--phase cluster` to retro-fix 96k unclustered listings, ~47% match rate looked too high and the log showed suspicious patterns (super-attractors, consecutive-ID burst matches). User asked to verify.

**Diagnosis**:
1. **Dealer-template phashes are everywhere** — one placeholder phash appears in **13,860 distinct listings** (14% of DB). Top 3 templates each ≥11,000 listings. These are dealer logo overlays / "no image" frames / watermarks that pHash treats as unique.
2. **Cross-make chimera clusters formed**: cid=2892 merged 10 listings spanning 9 different car models (Toyota Yaris, Skoda Octavia, BYD Song, Suzuki Vitara, BMW X7, Mercedes Vito, Citroen C5, Peugeot 208, Opel Corsa). Verified by inspecting the matching phashes: idx=2 phash `-4681333208439930270` (freq=11) appeared in BYD/Citroen/Peugeot/Opel; idx=3 `-5132463779871544018` (freq=12) same pattern.
3. **78 / 1295 multi-member clusters mix makes; 104 mix make+model** (~6-8% of all multi-member clusters were wrong).
4. **Counter-evidence**: cid=2504 (Peugeot 3008 ×6 super-attractor `65834572`) was legit — all members were genuine Peugeot 3008 2020/2021 relistings.

**Algorithm fix in `db/database.py:find_cluster_for_photos`**:
- **Template-phash exclusion**: a phash is a template iff it spans `≥ PHASH_TEMPLATE_MIN_MAKE_MODEL_SPAN` (=2) distinct (make, model) values. **Defined by make+model span, NOT by absolute frequency** — first attempt used `≥5 listings` as the threshold and wrongly flagged photos that appeared 5×+ from legit relistings of one car. The (make, model) span rule has zero collisions with legit single-car relisting (which always stays in one make+model). 6,138 template phashes detected on current data.
- **Make+model gate**: cluster join only allowed when candidate listing has same `make` AND same `model` (skip the gate when either side is NULL to avoid blocking listings with parser drops). Also makes the candidate scan ~100-300x faster by restricting via `idx_listings_make_model` instead of full-table scan.
- Process-lifetime cache on the template set with `invalidate_template_phashes_cache()` helper for tests.

**Pipeline integration**:
- `pipeline.py:313` passes `data["make"]` and `data["model"]` to find_cluster_for_photos.
- `scripts/backfill_phash.py:phase_cluster` queries make+model alongside photos and passes them through.

**Cleanup tooling**:
- New `scripts/reset_clusters.py` wipes `car_identity` + resets `listings.car_identity_id` / `relisted_from_listing_id`. Idempotent.

**Dry-run validation** (against the corrupted live DB before reset):
- Chimera cid=2892: all 9 members return None (0/3 non-template hashes survive after filtering).
- Legit cid=2504: all 6 members still cluster correctly; new algorithm even finds a 7th member (51902358) the broken one missed.
- Mixed-model cid=517 (Renault Captur + Renault Samsung QM3): all 4 members return None — cluster correctly splits.

**Files modified**: `db/database.py` (find_cluster_for_photos + helpers), `pipeline.py:313`, `scripts/backfill_phash.py:phase_cluster`. **New file**: `scripts/reset_clusters.py`.

**Outcome**: handed user three commands: (1) Ctrl+C the running broken cluster job, (2) `python -m scripts.reset_clusters`, (3) `python -m scripts.backfill_phash --phase cluster`. New run will be much faster (make+model-gated candidate scan) and correct (chimeras blocked).

**Post-rerun verification** (~6h later, 19:57):
- 99,458/99,458 listings clustered (100%).
- 83,371 clusters total; 12,893 multi-member relists detected (10× more legit relists than the broken algorithm found).
- Mixed-make: 78 → **2** (−97%). Mixed-make+model: 104 → 8 (−92%; 6 of those are `Make/None vs Make/Model` — likely legit merges with parser misses, not true chimeras).
- Top clusters all coherent dealer fleets: Hyundai Tucson ×82, Peugeot 3008 ×32, BYD models ×24 each.
- Screenshot Corollas confirmed merging: clusters 33892 (€4,999/228,578km Automată Gri ×2), 48759 (€4,899/370,202km Mecanică Gri ×2), 50923 (€4,700/280,000km Hatchback ×2).

**Two true chimeras root-caused** (cid=7414 Volvo+Opel, cid=21793 Skoda+Opel): the new `find_cluster_for_photos` returns None for those when re-run on current data, so the algorithm fix is sound. The chimeras formed because a long-running concurrent scrape process held the pre-patch `db.database` in memory (Python doesn't auto-reload imports). The OLD function had no template filter; V[1] vs O[1] hit Hamming=2 via template phashes, V[0] vs O[0] hit Hamming=6, two slots filled → match → cluster join.

**Belt-and-suspenders fix**: added a defensive cross-make/model guard inside `assign_cluster` itself. Even if `find_cluster_for_photos` returns a bad match (stale in-memory code, future bug, race), `assign_cluster` checks that the matched prior shares non-NULL (make, model) with the new listing before linking. Mismatch → falls back to singleton. Cannot form chimeras even by accident.

**Crash-handling tweak**: `phase_cluster` now retries on `database is locked` with exponential backoff (up to 6×, 2-30s) — same pattern as `phase_hash`. Caught when the user's run crashed at 96,258/99,291 due to WAL contention with the web app at 1.5GB WAL size.

**Cleanup tool**: `scripts/dissolve_chimeras.py` — finds true cross-make/model clusters, evicts minority members to singletons, leaves NULL-model clusters alone. `--apply` flag required to commit.

**Final files modified this session**: `db/database.py` (find_cluster_for_photos + _get_template_phashes + assign_cluster guard), `pipeline.py:313` (passes make+model), `scripts/backfill_phash.py` (passes make+model, lock-retry), `db/schema.sql` (new composite index). **New**: `scripts/reset_clusters.py`, `scripts/dissolve_chimeras.py`.

**Post-fix performance issue**: web UI hung on "loading..." after the backfill completed. Root cause: `web/queries.py` cluster-dedup `NOT EXISTS` subquery had no direct index for sibling lookup by `car_identity_id`. Pre-backfill 94% of rows had `car_identity_id IS NULL` so the OR-shortcircuit handled them and the subquery rarely ran. Post-backfill 100% of rows have `car_identity_id` populated → subquery fires for every row → falls back to `idx_listings_status_first_seen` (too wide). Items query hung >20s, count query worse.

**Fix**: `CREATE INDEX idx_listings_car_identity ON listings(car_identity_id, status, first_seen_at)`. Composite covers all subquery predicates → SQLite uses it as COVERING INDEX (`SEARCH sib USING COVERING INDEX`), never touches the base table. Post-fix: items_sql 0.00s (was hanging), count_sql 0.85s for 71,958 deduped rows (was >30s). Index added to `db/schema.sql` and live-applied to existing DB (no restart needed; SQLite auto-picks the new index on next query).

**Also surfaced**: WAL bloat. After 99k cluster assigns + reset + re-assign with web app actively reading, WAL hit 3.3 GB. Auto-checkpoint can only truncate up to the earliest open reader; constant web requests pinned that floor. Fix: stop web app, `PRAGMA wal_checkpoint(TRUNCATE)` from a fresh write connection, restart. Output `(0, 0, 0)` confirms full truncate. Steady-state operation doesn't trigger this — only one-shot mass mutations.

---

### [2026-05-24] Why duplicate Corollas weren't clustering — diagnosed `is_new`-gated cluster step
**What was asked**: User saw 4 near-identical dark Toyota Corolla 2005 listings (4,800€ / 4,850€ / 4,800€ / 4,800€, all 231,000 km, Diesel, Automată, Chișinău mun.) and asked why they weren't flagged as duplicates. Also noted that re-running `python -m scripts.backfill_phash --phase hash` said "nothing to hash".

**Diagnosis**:
1. **`--phase hash` is correct to be empty** — `100% of 1,166,179 photos already have a phash` (real or `-1` PHASH_FAILED sentinel). Query is `WHERE phash IS NULL`, so by design there's nothing left. Inline encoding in `scraper/photo.py:_encode_webp` + the PHASH_FAILED sentinel mean this step is permanently idempotent after first backfill.
2. **The actual bug**: `97.2% of listings (96,326 / 99,054) have car_identity_id IS NULL`. `pipeline.py:309-326` only calls `assign_cluster` when `is_new=True`. Every listing that existed before clustering was wired up just sits unclustered forever — refresh visits skip the cluster check.
3. **`seller_id` is NULL ~98% of rows** — only 1/90 Corolla candidates had a parsed seller_id ("NobilAuto-2"). The parser isn't extracting seller info reliably, which blocks any "seller + specs" fingerprint idea.
4. **UI collapse already works** — `web/queries.py:80-92` already filters cluster siblings down to one row in the grid. So once clustering catches up, the duplicates disappear automatically.

**What was done**: Backed up `listings.db` → `E:\DB\backups\listings-20260524-102707.db` (1.1 GB). Handed user the command `python -m scripts.backfill_phash --phase cluster` to run themselves. Confirmed script is resumable: per-listing `with db.connect() as conn:` block commits independently; Ctrl+C only rolls back the in-flight listing. Re-run picks up via the same `WHERE car_identity_id IS NULL ORDER BY first_seen_at ASC` query.

**Files modified**: none (diagnosis + DB ops only).

**Outcome**: User running cluster backfill manually. Expected 4–12 h for 96k listings. No threshold tuning yet — current Hamming ≤6 / ≥2 of first 3 photos is the working live config; retrocluster uses identical logic so no new false-positive risk.

**Open follow-ups**: (1) fix `seller_id` parser so the seller fingerprint becomes viable, (2) consider extending pipeline to call `assign_cluster` for legacy NULL-cluster listings on refresh path (self-healing), not just `is_new`.

---

### [2026-05-23] Browse side-card — fix median, add prank filter, generalize to "All listings"
**What was asked**: "you sure the median price is correctly calculated?" → discovered the SQL `OFFSET COUNT/2` returned the upper-middle value (not the average of the two middles) on even counts. Then: "exclude pranks like cars sold at -35% and higher" → add outlier filter. Then: "small 'i' icon on the median when hovering shows median of all listings" → info tooltip. Then iteratively: apply to active too; switch median to average; remove median entirely (avg only); finally, "make this info panel appear on any of the filter changes even if the model and make is not selected".

**What was done**:
1. **Median bug** — `web/analytics.py:425` used `ORDER BY price LIMIT 1 OFFSET COUNT/2` which is only correct for odd counts. With 4 sold prices `[18000, 22999, 27500, 27500]`, real median is 25249.5 but the query returned 27500 (offset=2). Replaced with Python-side computation that averages the two middles on even counts.
2. **Prank filter** — listings whose final (or current, for active) price dropped ≥35% from the original asking price are excluded from the cohort. Implemented by fetching `(MIN(recorded_at).price, MAX(recorded_at).price)` from `price_history` per listing and dropping rows where `final < first * 0.65`. Reason: typos / placeholder edits like "100 €" drag both median and avg sharply down.
3. **Info-icon tooltip** — small circled italic "i" next to the label on each price tile. Hover shows "Excludes N listings priced ≥35% below original asking price. Average of all: €X" so the user can see what was excluded and the unfiltered number.
4. **Iterations on stat type** — first added even-count median for sold, then median+prank for active, then user said "do avg not median", so both tiles became **Avg sold price** and **Avg active price** (true mean of prank-filtered set). The `_median()` helper was deleted in the final pass.
5. **Generalised to "no make/model selected"** — refactored `model_stats(make, model, ...)` to accept optional make/model; the SQL now composes an `mm_sql` fragment that drops the predicate when omitted. Endpoint (`web/app.py:398`) takes `make: str = "", model: str = ""`. Frontend (`web/static/app.js:162`) no longer hides the card when only filters (no make/model) are set; renders title as "All listings" / "BMW — all models" / "BMW 5 Series" depending on what's selected.

**Files modified**: `web/analytics.py` (median→avg, prank filter, dynamic make/model fragment), `web/app.py` (optional make/model query params), `web/static/app.js` (tile helper with info icon, dynamic title, drop the gate), `web/static/style.css` (`.ms-info` circled-i styling).

**Outcome**: Browse side-card now updates on every filter change regardless of make/model. Both Avg sold price and Avg active price are prank-filtered, with hover tooltips showing the unfiltered values + excluded count. Avg days to sell stays raw (no filter — it's a duration, not a price).

**Key decision**: see [[../decisions/999-CarScrapper-decisions|decisions 2026-05-23 — Prank filter]].

---

### [2026-05-18] Project bootstrap, perf tune, web UI, parser bugfix
**What was asked**: Build a 999.md car-listings scraper end-to-end (scraper → SQLite + WebP photos), then make it fast, then build a web UI to browse the data. Mid-session: the UI showed Next.js i18n JSON in the location field — fix it.

**What was done**:
1. **Initial build** — explored 999.md via agent-browser, designed schema with history tables for ML, wrote `scraper/{crawler,parser,photo,session}.py`, `pipeline.py`, `scheduler.py`, `db/{schema.sql,database.py}`. First test failed: listing-discovery crawler returned 0 IDs.
2. **Discovery rewrite** — found 999.md is a Next.js SPA; ID data is fetched client-side via `POST /graphql` op `SearchAds` (subCategoryId 659). Replaced HTML scraping with direct GraphQL calls. Detail pages stayed HTML-parsed (still SSR).
3. **Storage move** — relocated DB + photos from `Code/999 CarScrapper/data/` to `E:\DB\` via `DATA_DIR` env var (OneDrive sync was about to swallow 1 TB of WebPs).
4. **Performance** — diagnosed silent slowness: photos downloaded serially per listing, single global semaphore for site + CDN, jitter delay applied to CDN, Pillow blocking the event loop, WebP method 4. Fixed all five: per-host split semaphores, `asyncio.gather` over photos, `asyncio.to_thread` for Pillow, method 2. Benchmark went 510 s → 70 s (7.2× faster) for 156 listings + 2,336 photos.
5. **Web UI** — FastAPI backend with read-only SQLite (`mode=ro`) so it's safe alongside the scraper, vanilla-JS single-page frontend (~600 LOC JS, ~400 LOC CSS). Grid + table views, cascading make→model filter, multi-select chips, range sliders, detail modal with inline SVG sparkline for price history, dashboard tab with bar charts + price-drop leaderboard + sold-this-week.
6. **Location-leak bugfix** — `_extract_location` was matching the substring "Localitate" inside a `<script>` tag containing the Next.js i18n bundle, writing the entire 30 KB JSON dump as the `location` field for 1,706 of 1,709 rows. Identified true selector via agent-browser (`div[class*="map__address"]` → "Chișinău mun."). Fixed parser + added defence-in-depth: `parse_listing()` now decomposes `<script>/<style>/<noscript>/<template>` before any extractor runs. Cleared bad data with one UPDATE; kicked off `--refresh-known` to repopulate.
7. **Verified end-to-end in agent-browser**: grid renders 24 clean cards, detail modal shows 10-photo gallery + 46 spec rows, dashboard renders all charts.

**Key decisions**: see [[../decisions/999-CarScrapper-decisions|decisions]] — GraphQL for discovery, separate history tables per field, per-host semaphores, read-only DB for web app, vanilla JS, strip-scripts-first.

**Files created**: `config.py`, `pipeline.py`, `scheduler.py`, `scraper/{crawler,parser,photo,session,__init__}.py`, `db/{schema.sql,database.py,__init__}.py`, `web/{app,queries,__init__}.py`, `web/static/{index.html,app.js,style.css}`, `requirements.txt`, `README.md`, `.gitignore`.

**Files modified during session**: `scraper/parser.py` (3×: seller_type Romanian match; location selector fix; description selector + script-decompose), `scraper/session.py` (per-host semaphores), `scraper/photo.py` (parallelism + threadpool), `config.py` (twice: storage path; speed tunables), `web/app.py` (CTE alias bug `lp.recorded_at` → `lp.ra`).

**Outcome**: Working end-to-end. 1,709 listings scraped + ~14 k WebPs (~444 MB) on E:\. Web UI live at `http://localhost:8000`. Refresh-known crawl running in background to backfill cleared locations. Projected full 88k sweep: ~11 h.

---

### [2026-05-19] UI overlay-block fix, sold-detection rework, price-scrape bugfix
**What was asked**: "Site is not responsive — can't click anything." Then: "Some cars listed as sold are still active." Then: "Listings that don't really exist should be removed." Then: "Pay attention to what price you scrape — you took Prima rată as the price."

**What was done**:

1. **Overlay-blocks-clicks bug** — `.detail` modal had `display: grid` for centering, which overrode the user-agent `[hidden] { display: none }`. After closing the modal via `host.hidden = true`, the dark overlay stayed visible and intercepted every click. Fix: added `[hidden] { display: none !important; }` at the top of `style.css`.

2. **Sold-detection wording correction** — I had claimed listings on 999.md still render the car page when "sold". User corrected: truly deleted listings show "Anunțul nu a fost găsit" (not-found page). My earlier check matched "expirat" as a substring — but that string was the i18n KEY inside `<script>` JSON, not actual visible content. Re-verified by stripping scripts and reading body text.

3. **Verify-on-mark logic** — wrote `scripts/verify_sold.py`: for every `status='sold'` row, fetch URL and classify. Deleted page → DELETE from DB + photos + history rows + photo folder. Has specs → revert to active (false positive). Other → keep as sold. Ran it on the 4 existing sold rows: 1 was genuinely deleted (104357660 → deleted), 3 were false positives (reverted to active). Photo folder for 104357660 removed.

4. **Pipeline self-heals** — same verify logic baked into `pipeline.py` so future full-mode crawls run the verification on missing IDs automatically. Also added a 50%-discovery safety guard: if a crawl returns less than half the previously-known active set, skip the sold-marking step entirely (treat as partial crawl).

5. **UI relabel "Sold" → "Removed"** — covers expired/sold/hidden, more accurate. Added amber banner in detail view explaining what removed means and that 999.md may still serve the URL.

6. **Price-scrape bug** — `[class*="price"]` selector matched the wrapping div containing main price + old price + "Prima rată: 100 €" all together. Regex grabbed the first `<num> €` it found — sometimes the 100 € down-payment. 191 listings had prices <500 € (most at 1 €). Fixed: switched to specific selectors `[class*="price__main"]` (main) and `[class*="oldprice__value"]` (discount). Added new columns `old_price_eur` and `old_price_mdl` via live `ALTER TABLE`, updated `schema.sql` and `db/database.py` field list.

7. **Cleanup** — nulled 195 bad EUR prices + 11 bad MDL prices so the refresh-known pass repopulates them. Killed the running 13 GB scraper that had the old parser cached in memory, marked 3 orphan `status='running'` rows as failed, restarted a fresh full refresh.

**Key decisions**: see [[../decisions/999-CarScrapper-decisions|decisions]] — verify-missing-before-marking-sold, specific class selectors not wrapper, `[hidden] !important` guard, `ALTER TABLE` for solo SQLite migrations.

**Files created**: `scripts/verify_sold.py`, `scripts/__init__.py`.

**Files modified**: `web/static/style.css` (overlay guard + removed-banner), `web/static/index.html` (relabel), `web/static/app.js` (relabel + banner + isRemoved flag), `pipeline.py` (50% safety + verify-on-mark), `scraper/parser.py` (price selectors + old_price extraction), `db/schema.sql` (old_price columns), `db/database.py` (field list).

**Outcome**: UI clicks work again. DB cleaned: 0 sold orphans, 8,308 active listings. Parser now extracts main price + old price correctly. Verified end-to-end on 102253640 (VW Passat): main 15,990 € / old 19,000 € / EUR. Background refresh re-running with fixed parser.

### [2026-05-19] Pre-overnight: chunked memory-recycle refactor + README rewrite
**What was asked**: "Before I run the full crawl overnight, do a quick check for bugs." Then: "I have 32 GB RAM — can the scraper recycle its cache periodically?"

**What was done**:

1. **Pre-flight sanity check** — verified all 11 Python files parse, all imports resolve (including the late `from scripts.verify_sold` inside `pipeline.py`), schema/parser keys align (42 columns, 0 missing), E:\ has 2.4 TB free, ran a 1-page dry run (78 IDs, 24 new written, 260 photos, 0 errors). Cleared 8 more stale low-price rows from before the parser fix. Added `scripts/__init__.py` for cross-version package safety.

2. **Chunked memory-recycle refactor of `pipeline.py`** — the previous `asyncio.gather(*tasks)` over all 80k scrape targets created the entire task graph upfront and held it in memory until the run finished, plus httpx's connection pool grew unbounded. Restructured `run()` into three phases each with its own short-lived `Session` (discover, verify-missing, chunk-scrape), and the chunk-scrape phase now iterates `range(0, total, SCRAPE_CHUNK_SIZE)` with a fresh `Session` per chunk + `gc.collect()` between. Extracted `make_worker(session)` factory so each chunk's workers reference the correct session.

3. **Memory observability** — added `_mem_mb()` helper that tries `psutil.Process().memory_info().rss`, returns `None` gracefully if psutil isn't installed. Installed psutil. Per-chunk log line now reports RSS, so memory growth is visible in real time without Task Manager.

4. **Config** — added `SCRAPE_CHUNK_SIZE = 500` (tunable; 500 ≈ ~3 min per chunk at current rate).

5. **README rewrite** — full overhaul to reflect today's reality (was still describing the early-day state). New sections: GraphQL discovery, sold-detection-self-heals, chunk-recycle, Web UI, Maintenance subsection for `verify_sold.py`, `DATA_DIR` env override, all new config knobs, all design gotchas (SPA-vs-SSR split, script-strip-first, specific-price-selectors, import-cache trap, sold-≠-deleted, photo CDN path).

6. **Verified** — dry run with the chunked code path: 78 IDs found, 10 new, RSS=63 MB peak, "chunk 1/1 done" line emitted, 0 errors. All paths exercised.

**Key decisions**: chunk scrape targets to bound memory (instead of single-gather over 80k); per-chunk Session recycle to reset httpx pool; explicit `gc.collect()` after each chunk; psutil as optional dependency with graceful fallback.

**Files modified**: `pipeline.py` (full `run()` refactor), `config.py` (added `SCRAPE_CHUNK_SIZE`), `README.md` (rewrite), `scripts/__init__.py` (new, empty).

**Outcome**: scraper is ready for the overnight `--mode full --refresh-known` run. Projected: ~88k listings × ~3 s with photos ÷ 8 workers ≈ 8–10 h, RSS expected to stabilize at a few hundred MB instead of climbing to 13 GB. Per-chunk log line every ~3 min so progress is visible.

---

### [2026-05-19] First-page perf, destructive-delete catastrophe, full audit history, optional-features extraction, lxml speedup, analytics + ML dashboard

**What was asked**:
1. The web UI's first page wouldn't load with 88k listings.
2. Investigate why `listings_sold=0` despite 235 missing from discovery.
3. Implement smart-refresh for `--refresh-known` (3h is too slow).
4. **"do whatever you want, but i dont want to miss if the listing is modified, pictures or description"** — user discovered `verify_sold.delete_listing` was actually `DELETE FROM listings + shutil.rmtree(photos)` — 235 cars wiped that day. Asked for everything to be preserved.
5. Add catch-all history for every field change, not just price/mileage/desc.
6. Add scraping of optional features (Securitate + Confort sections).
7. **Big extension**: dashboard analytics (sell-through, value retention, drop effectiveness, DOW trends, stuck inventory), Analysis tab with ML predictors (fair price + days-to-sell), hot-deals feed, per-card DEAL/PRICEY badges, redesigned Favorites tab.

**What was done**:

1. **Web UI perf** — diagnosed `/api/facets` running 7 full-table GROUP BYs + `/api/stats` 5 more + missing `idx_listings_status_first_seen` index. Added 8 composite indexes + expression index `date(first_seen_at)`. Added in-process TTLCache (60s) on `/api/facets`, `/api/stats`, `/api/makes`, `/api/models`, and the unfiltered `COUNT(*)`. Replaced correlated thumb subquery with LEFT JOIN. First-page load now sub-second.

2. **The sold/deleted bug** — read `pipeline.py:78-108` and `verify_sold.py`: `page_state()` returns `'deleted'` for the "Anunțul nu a fost găsit" page, which then triggers `delete_listing(conn, lid)` — a function that hard-deletes the row + history + photo folder via `shutil.rmtree`. The `'sold'` bucket only fires for the "unknown" page state, which never actually happens on 999.md. So *every* removed listing was being destroyed by design.

3. **Soft-archive** — rewrote `delete_listing` to `UPDATE listings SET status='removed', removed_at=datetime('now')`. Added `removed_at TEXT` column via ALTER. Kept the function name to avoid breaking callers. Updated UI: `status='removed'` now displays under the "Removed" tab alongside legacy `'sold'`. `pipeline.py` logs the IDs of newly-archived listings each run. Added `scripts/backup_db.py` (SQLite online-backup API) + hooked into pipeline so every `--mode full` snapshots `listings.db` to `E:\DB\backups\` first (last 14 kept). Tried `scripts/recover_orphans.py` against 9 orphan photo folders — all 9 were empty shells (rmtree had wiped their contents) and 999.md returned "not found" for all of them. The 235 cars deleted earlier in the day were unrecoverable from local sources; recommended Volume Shadow Copies / Recuva.

4. **Catch-all field history** — added `listing_field_history(listing_id, field, old_value, new_value, recorded_at)` table + `photo_history(event, idx, filename, original_url)`. Wired `update_listing` to diff all 33 scalar fields; `insert_photos` to diff added/removed/replaced slots. `touch_seen`, `mark_sold`, and soft-archive log status transitions. Verified live by editing title+color on listing 4942 (round-trip captured 4 rows correctly).

5. **Optional features** — built `FEATURES_CATALOG` (49 labels across Securitate + Confort, with Unicode normalisation for ş/ș cedilla-vs-comma drift). Added `listing_features` + `feature_history` tables. Parser collects all short text fragments and matches against catalog. Verified live on Skoda Superb (104141672) → 17 Securitate + 17 Confort, exact match with the user's screenshot.

6. **lxml + asyncio.to_thread** — switched BS4 to lxml parser (~3-5× faster: 150 ms → 40 ms per listing) with graceful html.parser fallback. Wrapped `parse_listing` in `asyncio.to_thread` so the BS4 work doesn't block the event loop while other workers do I/O.

7. **Scraper field additions** — probed live page: `view_count` is JS-injected (would need `AdViews` GraphQL call per listing — deferred), `Negociabil` doesn't actually exist as a 999.md flag (was a screenshot misread). Kept `site_updated_at` (parsed from "Actualizat: 19 mai. 2026, 13:05" with RO month map) and `offer_type` (Vând / Cumpăr / Auto la comandă — useful filter dimension). Added both as columns + to `UPDATE_FIELDS` so they go through the history diff loop.

8. **Analytics + ML dashboard extension** (planned via plan mode, then implemented in 11 tracked tasks):
   - **`web/analytics.py`**: 7 endpoints (KPIs, days-to-sell-by-make, drop effectiveness, value retention, sell-through heatmap, DOW trends, stuck inventory). All 60s TTL-cached. Outlier-filtered (`price_eur >= 500`, `|drop_pct| <= 90` — defends against the legacy 1-EUR Prima-rată parser-bug listings). Designed grouped charts to always include `n` sample size so the frontend can grey out under-5 cohorts.
   - **`web/ml.py`**: sklearn Pipeline (Ridge + OneHotEncoder + StandardScaler), gated at 500 archived listings, daemon-thread retrain every 24h. XGBoost auto-detected if installed. Pickles to `E:\DB\models\{fair_price,days_to_sell,meta}.pkl`. `predict_price` clamped to [€500, €500k] to defend against mileage-outlier listings (10M km typos). After each retrain fills `price_predictions(listing_id, predicted_eur, delta_pct, flag)` cache for all ~85k active listings in ~5s.
   - **Frontend**: added Chart.js 4.4 CDN, new "Analysis" tab (ML status gate / predictor forms / hot-deals feed / drop scatter), Browse tab "Deals only" toggle + per-card DEAL/PRICEY badges, Favorites tab refresh (header stats + grid/list toggle + sort). Migrated existing custom HTML bar charts to Chart.js. CSS variables thread theme tokens through chart colors.
   - **Live verification**: trained on actual 407 archived rows (temporarily relaxed threshold), R²=0.859, MAE=€2,554. BMW 320d 2017 / 150k km → €17,959 ± €2,554. dealsOnly filter narrows 88,862 active → 22,126 deals. Land Rover Discovery Sport listed €9,550 vs predicted €15,900 = -40% deal.

**Key decisions** (see decisions doc): soft-archive over hard-delete (after the 235-row loss); reused `cached()` helper for analytics; one denormalized `price_predictions` cache table (not on-the-fly inference); 500-row training gate with frontend "collecting data" placeholder; in-process daemon thread for retrain (no extra process); BS4 + lxml fallback chain; matched feature catalog rather than free-form parse.

**Files created**: `scripts/{backup_db,add_web_indexes,recover_orphans,verify_sold (rewrote),train_models}.py`, `web/analytics.py`, `web/ml.py`, `web/static/` (Chart.js + Analysis view).

**Files modified**: `scripts/verify_sold.py` (destructive → soft-archive), `pipeline.py` (pre-run backup + log archived IDs), `db/schema.sql` (`removed_at`, `site_updated_at`, `offer_type`, `listing_field_history`, `photo_history`, `listing_features`, `feature_history`, `price_predictions`), `db/database.py` (catch-all field diff in `update_listing`; photo diff in `insert_photos`; status-transition logging in `touch_seen`/`mark_sold`; features sync), `scraper/parser.py` (lxml; feature extraction with Unicode normalization; `site_updated_at`; `offer_type`), `web/app.py` (TTLCache, analytics + ML endpoint registration, startup hook), `web/queries.py` (`dealsOnly` filter; join to `price_predictions`; thumb LEFT JOIN), `web/static/{index.html,app.js,style.css}` (Analysis tab, deals toggle, badges, favorites refresh, Chart.js helper), `requirements.txt` (lxml + sklearn + numpy + pandas), `README.md` (new Analytics & ML section + 4-tab UI description + Captured fields update).

**Outcome**: 88,862 active + 559 archived. Web UI loads instantly. ML models trained (R²=0.859, sample 407 — temporarily under the 500 gate for testing). 22,126 active listings flagged as deals, 30,409 as pricey. Every scalar field change + photo change + feature change + status transition is now permanently captured in append-only history tables. Nothing destructive remains in the pipeline. Plan file: `~/.claude/plans/you-are-building-a-fluttering-trinket.md`.

---

### [2026-05-19, late] Analytics SQL perf, ML junk data, dashboard layout collapse, parallel scraping (and why it didn't help), Analysis-tab redesign

**What was asked**:
1. Dashboard analytics looked buggy — charts on the left side, "continuously growing", deals/pricey prices looked hallucinated.
2. Add parallel scraping for the 5h full sweep.
3. PowerShell helper for parallel (then `--fast`, `--refresh-older-than`).
4. Analytics tab UI hated — wanted a redesign.
5. After `--fast`: "it's not fast at all" → debug throughput.
6. Save to vault.

**What was done**:

1. **Dashboard layout collapse** — the `.layout` grid is `260px 1fr` (filters + main). When the filter sidebar gets `display:none`, the 260px column stays reserved, and CSS Grid auto-flowed `#dashboardView` / `#analysisView` / `#favoritesView` INTO that 260px column. Fixed with `.filters{grid-column:1}; .results{grid-column:2}` + `body[data-tab]` driven CSS that collapses to `1fr` on non-Browse tabs.

2. **Chart.js infinite-grow bug** — canvases had `height="220"` attribute but no CSS height. With `responsive:true, maintainAspectRatio:false`, Chart.js fills its parent; the parent `.dash-card` had no height, so each resize observer tick grew the canvas. Wrapped every `<canvas>` in `<div class="chart-box">` with `position:relative; height:240px` and `.chart-box.tall { height: 320px }` for the scatter.

3. **Bogus "deals" investigation** — user asked "where did you take the prices?" Top 5 deals were ALL garbage: Mitsubishi 10M km, Dacia 65M km, Mercedes €1,111,111 — seller typos. The model produced €488k predictions (clamp max) and they showed as -100% deals. Root cause: training data + prediction cache both included junk inputs. Fixed with filter `year IS NOT NULL AND year BETWEEN 1980-2030 AND mileage_km BETWEEN 1000-500000 AND price_eur BETWEEN 500-200000` in BOTH `_load_removed` AND `_fill_price_predictions`. Plus `delta_pct > -90 AND < 500` so the model can't flag listings that hit prediction clamps. Retrained: R² 0.859→0.873, MAE €2554→€2193, deals 22k→18k (legitimate cheap listings now).

4. **Analytics SQL perf** — `/api/analytics/kpis` was hanging 90+ seconds. Cause: correlated subquery `(SELECT COUNT(*) FROM price_history WHERE listing_id = l.id) >= 2` ran once per listing (O(N²) over 88k). Also `sell_through_heatmap` did 285 individual COUNTs (15 makes × 19 body_types). Rewrote both: kpis 9.5s → 477ms; sell_through 9.3s → 700ms via single-pass `GROUP BY`. Also ran `ANALYZE` against the live DB so SQLite's query planner has fresh stats for the new history tables.

5. **`renderKpis` no longer blocks listings** — was `await`ing both /api/stats AND /api/analytics/kpis before the listings grid fetched. Cold kpis = 9s = page looked dead. Now: paint stats KPIs immediately, lazily upgrade with analytics ones via `.then()`.

6. **Parallel scraping `--shard N/M`** — added to `pipeline.py` with manifest-based discovery sharing: lead writes IDs to `E:\DB\manifest-discovery.json`, followers wait + read. Created `scripts/run_parallel.ps1` helper. **But empirically, sharding hurt**: at 4 shards the user's 4th got 429'd and total throughput stayed flat. 999.md rate-limits per IP, so N processes split the same throttled pipe N ways AND each independently re-runs the GraphQL crawl. Conclusion: single fast process beats sharding.

7. **GraphQL introspection** for smart-refresh — confirmed `Advert` type exposes `posted/reseted/expire/state/title`. **But** `reseted`/`posted`/`expire` always return empty strings for unauthenticated callers. `getAdsByIds` returns `UNAUTHENTICATED`. The timestamp-based smart-refresh that'd cut refresh to <15min needs an authenticated session. Deferred. Could fall back to title-diff (cheaper signal) but didn't ship.

8. **Speed bug #1 — `--fast` was a no-op.** `Session(site_concurrency=config.CONCURRENT_REQUESTS)` evaluates the default at module import time, before `pipeline.run()` mutates it. Fixed by reading `config` inside `__init__`.

9. **Speed bug #2 — global `sem_lock` serialized 16 workers down to 1.** The entire DB-write + log block per worker was `async with sem_lock:`. With 16 workers spawned, only 1 could be in that block at a time. Removed entirely (CPython dict updates are atomic under the GIL, SQLite WAL handles its own writer serialization). Net effect: from 2.7 listings/s to ~5.4/s with same network.

10. **Speed bug #3 — `update_listing` did the full 40-column UPDATE + 30-row feature DELETE/INSERT every time, even when nothing changed.** Added a fast-path: if no scalar fields changed AND description unchanged, just `UPDATE last_seen_at, last_fetched_at` (one tiny statement) and return. Same for `_sync_features`: if `new_set == prev_set`, skip the DELETE+INSERT entirely.

11. **CDN HTTP/2 → HTTP/1.1** — user's log showed `StreamReset stream_id:N error_code:1` from i.simpalsmedia.com. Caused by too many h2 streams multiplexed over one connection. Switched httpx client to `http2=False`; h1.1 over many TCP connections gives the same throughput without the protocol resets.

12. **999.md soft-throttle discovery via empirical benchmark** — benchmarked sem=16 (p50 1,065ms per HTTP), sem=24 (p50 12,795ms — 13× slower). 999.md actively slows responses when you push hard; the ceiling is ~12-16 concurrent. Recalibrated `--fast` to sem=12 delay=(50,150) and added explicit help-text warning.

13. **`--refresh-older-than HOURS` flag** — incremental refresh: only re-fetch listings whose `last_fetched_at` is older than N hours. The honest answer to "make refresh faster" without auth: don't refresh every listing every day. Steady-state nightly run finishes in minutes.

14. **Analysis tab UI rewrite** — user said the original was bad. Issues found: massive empty left column (the 260px collapse bug from #1), 5 mini-KPIs including ugly "TRAINED 2026-05-19 13:11" tile, two identical predictor cards (Fair Price + Days-to-Sell stacked), 13 inputs flat in one grid, no live feedback, useless scatter (~13 points). Rewrote as: one-line ML status banner with collapsible "How does this work?" explainer (the user explicitly asked for this), two-column layout (predictor left / hot deals right), grouped form fields (CAR / TECH / SPEC / CONTEXT), live debounced auto-predict (no submit button), combined predictor returning BOTH price and days-to-sell, colored verdict tile (DEAL / A BIT LOW / FAIR / A BIT HIGH / PRICEY), filterable deals feed (max € + make dropdown).

15. **Removed misleading `listings_deleted` stat key from pipeline run summary.** User's eye landed on `'listings_deleted': 85` after a run and panicked (PTSD from the 235-row catastrophe). The key was legacy backwards-compat alongside the correct `listings_removed: 85`. Killed it.

**Key decisions** (see decisions doc): sharding can hurt when source server throttles per-IP; fast-path early-exit in update_listing for unchanged refreshes; HTTP/1.1 beats h2 multiplexing for moderate-concurrency mixed workloads; never trust default-arg config reads in async code; cache predictions for active listings (don't infer per-request).

**Files modified**: `web/analytics.py` (kpis/drop_eff/value_retention/sell_through rewritten single-pass), `web/ml.py` (junk filter + flag bounds), `web/queries.py` (predictor join), `web/app.py` (faster cache), `web/static/{app.js,style.css,index.html}` (layout fix, chart-box, redesigned Analysis), `pipeline.py` (`--shard` manifest, `--fast` recalibrated, `--refresh-older-than`, dropped `sem_lock`, dropped `listings_deleted` key), `scraper/session.py` (config read at construction, HTTP/2 → 1.1), `db/database.py` (fast-path for unchanged refreshes + targeted feature diff), `scripts/run_parallel.ps1` (new).

**Outcome**: Dashboard renders full width with bounded charts. Deals feed shows real listings only (junk filtered). Analytics endpoints all sub-second after `ANALYZE`. Refresh throughput doubled (2.7→5.4 listings/s); a full refresh now projects ~4.5h, an incremental `--refresh-older-than 24` projects ~15 min. Real ceiling is 999.md's soft throttle, not local code. Smart-refresh via GraphQL is dead without auth (introspection confirmed).

---

### [2026-05-21] USD support, mid-run deletion detection, fast-by-default, tick verify-missing

**What was asked**:
1. Decode this log line: `[16520/89840] upd 104380041 ? ?y ?€ (0 photos)` — what is it, will it be categorized as deleted?
2. Make `pipeline.py --mode full` run as fast as the scheduler does, and capture USD prices that some listings use.
3. Have the scheduler's tick also archive deleted listings (since it already paginates every page).

**What was done**:
1. **Decoded the `?` line** — `upd` = known listing refresh; `?` = parser returned all-None for make/year/price; `(0 photos)` is the normal refresh path (photos only fetched for new listings). Under the OLD code this was NOT being marked deleted — it silently overwrote real DB columns with NULL. Root cause: 999.md returns an "Anunțul nu a fost găsit" page when a listing is deleted between discovery and the detail-fetch later in the same run; parser dutifully returns an empty dict; `update_listing` writes the empties.
2. **Mid-run deletion detection** — `pipeline.py` worker now calls `_is_stub(data)` (no make AND no price in any currency). On refresh: soft-archive via `scripts.verify_sold.delete_listing`, increment `listings_removed`, log `DEL <id> (deleted mid-run)`. On NEW: just count as error, skip insert. The `?` log noise is gone — line now conditionally prints only fields that exist, with `€`/`$`/`MDL` based on which currency was captured.
3. **USD natively** — schema gained `price_usd` and `old_price_usd` on `listings`, `price_usd` on `price_history`. Parser regex extended to match `\$|USD`. `_parse_prices()` returns 4-tuple `(eur, mdl, usd, listed)`. `init_db()` runs additive `ALTER TABLE` wrapped in `try/except OperationalError` so existing DBs upgrade in place on next start. Threaded through `UPDATE_FIELDS`, `price_changed` diff, `_record_price()`, both insert/update call sites.
4. **Fast-by-default** — flipped `pipeline.run(fast=False)` → `fast=True`. `--fast` is now a no-op (already on); `--no-fast` is the new opt-out. Closes the gap where shell-invoked full runs were running at sem=8 while the scheduler's tick/incr were at sem=12 with delay=(50,150).
5. **Tick runs verify-missing** — `if mode == "full":` widened to `if mode in ("full", "tick"):`. Scheduler_f's 10-min tick already does a full GraphQL discovery sweep (max_pages=None), so the `known_active - crawled_ids` diff is meaningful. The 50% discovery safety guard still applies. Removed listings now archive within minutes instead of waiting for Sunday's `full`.

**Note**: A full refresh was running while these edits happened. Python had the old module loaded → that in-flight run still wrote the `?` noise and overwrote NULLs for mid-run deletions. Recovery: any active row with no price after that run finishes can be re-archived by the next `tick`'s verify-missing or by running `scripts/verify_sold.py`.

**Files modified**: `db/schema.sql` (3 new columns), `db/database.py` (migration + USD threaded through update/insert/_record_price), `scraper/parser.py` (regex + 4-tuple + both call sites), `pipeline.py` (`fast=True` default, stub detection in worker, `?`-free log line, verify-missing in tick, `--no-fast` flag).

**Outcome**: The silent NULL-overwrite bug is fixed at the source. USD-listed cars (previously invisible to all price-based queries / ML training / deals filter) are now first-class. `python pipeline.py --mode full` is as fast as scheduler ticks by default. Deleted listings get archived every 10 min instead of weekly.

---

### [2026-05-21] Web UI: USD display, Period field, portrait photos, cache-bust headers

**What was asked** (continuing the same day's session):
1. Mercedes S-Class 102884703 shows "price n/a" even though it's listed in USD on 999.md.
2. Add a `[date_found]-[date_ended]` "Period" field to each listing (modal only).
3. "Nothing changed" — even after restart/incognito, JS edits aren't reaching the browser.
4. Portrait (9:16) photos overflow the modal and get cropped at the bottom.
5. Move the Period label to the top-right area next to the price; shift the price left.

**What was done**:
1. **USD on the web layer** — `web/queries.py` SELECT now returns `price_usd`; sort `COALESCE(price_eur, price_usd, price_mdl/19.0)`; price filter accepts `currency=USD`. `web/app.py` price-history endpoint includes `price_usd`. `web/static/app.js` `fmtPrice(eur, mdl, usd, cur)` displays `$37,850` (backwards-compatible 3-arg shim for old callers). All six call sites upgraded. Result: 2,106 active listings now display USD prices correctly.
2. **Period field** — Added `_ddmmyyyy()` + `fmtPeriod(it)` helpers in `app.js`. Active → `dd/mm/yyyy - current`; sold/removed → `dd/mm/yyyy - dd/mm/yyyy` (sold_at || removed_at || last_seen_at). Rendered in the modal spec list and now ALSO in the top-right of the price block.
3. **Cache-bust the JS/CSS pipeline** (the "nothing changed" problem) — three layers:
   - `web/app.py` `index()` rewritten as `HTMLResponse` that injects `?v=<mtime>` into the `/static/app.js` and `/static/style.css` URLs based on file modification time.
   - HTML response itself sends `Cache-Control: no-cache, no-store, must-revalidate` so the browser always re-fetches the (versioned) script/link tags.
   - New `NoCacheStaticFiles(StaticFiles)` subclass sends `Cache-Control: no-cache` headers on every JS/CSS response (belt-and-suspenders for stuck Chrome disk cache).
4. **Portrait photo fit** — `.detail-photos .main-photo` switched from `display: grid; place-items: center; height:100%` + `img { width:100%; height:100% }` to `display: flex; align-items: center; justify-content: center` + `img { max-w:100%; max-h:100%; width:auto; height:auto }`. The old grid setup hit a circular sizing dependency where a 432×960 portrait image inflated the row to 1414px tall and overflowed the 522-tall modal. New CSS lets the browser size the image to its natural aspect ratio capped by the container — portrait photos letterbox horizontally, landscape fills width.
5. **Period in the top-right header** — Wrapped `.detail-price` in a new `.detail-price-row` flex container with the `.detail-period-badge`; `justify-content: space-between` puts price on the left, period top-right. `.detail-price-block` changed to `align-items: stretch` with `min-width: 320px` so the row has room.

**Diagnostic process** for the "nothing changed" debugging: used agent-browser MCP to load the user's exact URL and `eval()` to dump modal DOM and computed styles. Confirmed at every step that the SERVER served fresh content (curl + grep) and the AGENT-BROWSER rendered correctly — proving the issue was purely user-browser disk cache. Eventually added the no-cache headers because version-busting alone wasn't reaching their browser.

**Files modified**: `web/queries.py` (USD column + sort + filter), `web/app.py` (price_history SELECT + HTMLResponse index + NoCacheStaticFiles), `web/static/app.js` (fmtPrice 4-arg, fmtPeriod, modal markup with price-row + period badge), `web/static/style.css` (.detail-photos .main-photo flex rewrite, .detail-price-block/.detail-price-row/.detail-period-badge).

**Outcome**: USD-listed cars now display prices in the UI. Modal shows lifetime period in the top-right. Portrait photos no longer overflow. Future JS/CSS edits cannot be defeated by Chrome cache — three independent mechanisms (mtime version, HTML no-cache, static no-cache) all guarantee fresh fetches.

**Note on uvicorn**: changes to `web/app.py` require uvicorn to reload. If running without `--reload`, must be killed and restarted manually. Static file changes (CSS/JS) don't need a restart — they're re-read from disk each request.

---

### [2026-05-22] pHash relisted-car clusters + Removed-tab pagination + model/popularity analytics + cohort-card restyle

**What was asked** (single long session, six threads):
1. Implement the README todo "Photo perceptual hash (pHash) — detect relisted cars with new IDs". User asked for the design first; I proposed **(b) link-don't-merge** with a `car_identity` cluster + `relisted_from_listing_id` pointer, priority on the newest member but all data preserved, cluster marked removed only when every member is gone.
2. Removed tab paginates as 3,400 pages even though only ~200 have rows. Fix.
3. Add per-(make, model) analytics: cohort side card in Browse + Dashboard popularity tile.
4. When the status toggle flips to Removed, the Make/Location dropdowns still show counts of ALL listings — make them scope to the active status.
5. Add a "Sold by model year" breakdown to the cohort card; make every stat respond live to sidebar filters (year range, fuel chips, etc.).
6. Restyle the cohort card — year chips read as one run-on string ("2007 · 32008 · 5…"); 6 stat tiles look like 6 separate boxes. Use ui-ux-pro-max skill.

**What was done**:

— **pHash + cluster**: added `photos.phash` (signed 64-bit), `car_identity` table (`id, first_seen_at, last_seen_at, listing_count, current_listing_id, status, removed_at`), and `listings.car_identity_id` + `listings.relisted_from_listing_id`. `db/database.py` got `find_cluster_for_photos` (Hamming ≤ 6, ≥ 2 of first 3 photos match), `assign_cluster` (joins existing cluster or creates a singleton; new listing becomes `current_listing_id`), and `reconcile_cluster_status` (cluster → `removed` only when no member is still active). `mark_sold` and `verify_sold.delete_listing` both call `reconcile_cluster_status`. `scraper/photo.py` runs `imagehash.phash` during WebP encode and threads the value through. `scripts/backfill_phash.py` is a two-phase one-shot: hash existing webp files in batches, then cluster historically ordered by `first_seen_at`. `requirements.txt` got `imagehash>=4.3`. UI: `/api/listings/{id}` returns a `cluster: {members, listing_count, first_seen_at, last_seen_at}` object when ≥ 2 members; detail modal renders a "🔁 Relisted N× — same car first seen YYYY-MM-DD, K days on market total" badge with clickable twin chips.

— **Removed-tab pagination**: `web/queries.py` now flips `has_user_filters = True` when status is `sold`/`removed`/`all`, so `web/app.py:/api/listings` runs a real `COUNT(*)` over the filtered set instead of reusing the cached active count. The Removed tab now paginates the ~6,861 removed rows correctly.

— **Model analytics endpoints**: `web/analytics.py` got `model_stats(make, model, recent_days, filters)` and `popularity(days, limit)`. `model_stats` returns active, sold_total, sold_recent, median_sold_eur, avg_price_active_eur, avg_days_to_sell, sold_by_year (list of `{year, count}` — years with zero sales excluded by GROUP BY), and `filters_applied`. `popularity` returns ranked `(make, model)` by archived count in a rolling window plus a velocity %.

— **Status-scoped facets**: `/api/facets` and `/api/models` accept a `status` param. `_status_where(status)` returns the SQL fragment. Cache keys include status. Frontend forwards `state.filters.status` and the status toggle re-runs `loadFacets()` (restoring prior make/model selection if still valid) before refetching listings.

— **Filter-aware cohort card**: new helper `build_extra_filters(params, alias="")` in `web/analytics.py` mirrors the parsing in `web/queries.py` (year/price/mileage/engine ranges, fuel/transmission/drive/body/color multi-selects, seller_type, location, q). Accepts an `alias=` so the aliased median-price subquery reuses the same args. `model_stats` threads the fragment through every sub-count. Endpoint param-filter strips listing-only keys (`page`/`page_size`/`sort`/`sort_dir`/`status`/`dealsOnly`) so they don't bust the cache. Frontend passes the full `buildQuery()` — every filter change already triggers `fetchListings → renderModelStatsCard`, so the tile refreshes in lockstep.

— **Cohort card restyle** (ui-ux-pro-max skill): root cause of the broken-looking chips was the previous CSS referencing undefined variables (`--card`, `--divider`, `--bg-elevated`). Fallback colors barely registered, so chip borders/backgrounds dissolved into a run-on string. Rebuilt against the project's real token set (`--surface`, `--surface-2`, `--surface-3`, `--border`, `--accent-soft`, `--accent-border`). New layout: ONE composed surface with internal hairline dividers between 6 stat tiles (bento feel, no individual boxes). Header carries make+model title plus two pill chips (window in neutral `--surface-2`; "matching filters" in `--accent-soft`/`--accent-border` when sidebar filters narrow the cohort). Stat values use `font-variant-numeric: tabular-nums` + `letter-spacing: -0.015em` for column alignment. Year chips render as `<b>year</b><i>count</i>` so the year is full text color and count fades to soft — eye instantly pair-groups them. Year section gets a subtle `color-mix(--surface 60%, --bg)` background. Grid collapses 6 → 3 → 2 columns at 1100 / 600 px.

**Key decisions**:
- **Link-don't-merge** for relisted cars (option b over option a "replace/merge" and c "just-flag"): preserves price/desc/photo deltas across reincarnations, exposes the dealer tactic in the UI, lets ML treat "real days on market" as cluster lifetime instead of newest listing's age.
- **Stored phash as signed 64-bit** — SQLite INTEGER overflows on unsigned u64 (got `OverflowError: Python int too large to convert to SQLite INTEGER` on first backfill run). XOR-based Hamming is bit-identical so comparison is unaffected. Wrap: `if u >= 2**63: u -= 2**64`.
- **Cohort card reacts to sidebar filters but NOT to status toggle** — `model_stats` always reports both Active and Sold, regardless of which tab is current. The "matching filters" tag only appears when extra sidebar filters scope the data.
- **ALTER migrations run BEFORE `executescript`** in `init_db`. schema.sql now contains the new `idx_photos_phash` index which references a column the existing DB doesn't have yet. The reorder lets the additive migration add the column first, then executescript creates the index. (Was: ALTERs ran AFTER executescript, which failed on the index DDL.)
- **`build_extra_filters` with optional alias** instead of string-replacing column names in a copy of the WHERE — built-in alias prefixing is the clean way to share filter logic across queries that JOIN the `listings` table aliased.

**Files changed**:
- `db/schema.sql` — `photos.phash`, `car_identity` table, indexes
- `db/database.py` — migrations re-ordered before `executescript`, `find_cluster_for_photos` / `assign_cluster` / `reconcile_cluster_status`, `insert_photos` writes phash, `mark_sold` reconciles
- `scraper/photo.py` — `imagehash.phash` during encode, signed-int wrap
- `pipeline.py` — cluster assignment after `insert_photos` for new listings
- `scripts/verify_sold.py` — soft-archive calls `reconcile_cluster_status`
- `scripts/backfill_phash.py` (new) — `--phase hash | cluster | all`
- `requirements.txt` — `imagehash>=4.3`
- `web/queries.py` — non-`active` status flips `has_user_filters`
- `web/app.py` — `_status_where`, `/api/facets?status=`, `/api/models?status=`, `/api/analytics/model_stats`, `/api/analytics/popularity`, listing detail returns `cluster`
- `web/analytics.py` — `build_extra_filters(params, alias)`, `model_stats(filters=)` + `sold_by_year`, `popularity()`
- `web/static/app.js` — `renderModelStatsCard` forwards full filter set + renders year chips, status toggle reloads facets, relisted badge + clickable cluster-chip handler in detail modal, popularity tile in Dashboard
- `web/static/index.html` — `#modelStatsCard` container above grid
- `web/static/style.css` — cohort card rebuilt (bento layout, real tokens, tabular-nums); detail-modal cluster CSS

**Outcome**: pHash backfill runnable (`pip install imagehash; python -m scripts.backfill_phash --phase all`); every new pipeline run auto-clusters. Removed tab paginates correctly. Cohort card reads as one composed surface and reacts live to every sidebar filter; year chips show only years with actual sales. Two runtime bugs caught and fixed mid-session: `executescript` migration order, and phash u64 → SQLite signed-int overflow.

---

### [2026-05-23 — later session] Cluster as unit of truth: merge relisted, exclude from Sold, fix Active mismatch, themed chart + scrollbars

**What was asked**: a Lada BA3 2108 showed up in BOTH the Removed tab (deleted listing `#104128799`) AND as an active listing (`#104436026`) — same physical car. User wanted:
1. Merge the deleted listing into the active one: combined price history, cluster first-seen, list of all ids, plus this-listing's own first-seen.
2. Render price history as a proper chart (X = date, Y = price, visible points).
3. Active relisted cars must NOT appear in Removed tab.
4. Add an `i` info icon next to "Sold (window)" showing total deletion count vs truly-sold count.
5. Theme the scrollbars (modal vertical, filter rail, thumbnail strip) — default Windows white-on-dark was jarring.
6. Top-bar KPI showed 86,169 active but model-stats card said 89,635 — fix the discrepancy and surface duplicates count via an `i` tooltip on the Active tile.

**What was done**:
1. **`web/queries.py`** — Removed/Sold filter gained `NOT EXISTS (SELECT 1 FROM listings sib WHERE sib.car_identity_id = listings.car_identity_id AND sib.status='active')`. The deleted half of a relisting is now hidden whenever the physical car is currently active.
2. **`web/app.py:get_listing`** — when `cluster` exists (≥2 siblings), fetches `price_history` + `mileage_history` from EVERY sibling in one `IN (?, ?, ...)` query and returns them as one chronologically-sorted list tagged with `listing_id` per point. Added `cluster.first_seen_at_overall` (oldest member's `first_seen_at`) + `cluster.listing_ids`.
3. **`web/analytics.py`** — three changes: (a) module-level `_NOT_BUYER` constant + folded into `REMOVED_FILTER`, (b) `sold_recent_truly` / `sold_total_truly` mirror the Removed-tab exclusion, plus `relisted_recent` / `relisted_total` for the info-tooltip gap, (c) Active count flipped to `COUNT(DISTINCT COALESCE(car_identity_id, -id))` for unique cars, plus `active_total_listings` + `active_duplicates` fields.
4. **`web/static/app.js`** — `renderHistoryChart()` Chart.js helper for price + mileage history (time scale, 4px points, cluster siblings dimmed grey vs accent-colored own points, tooltip shows date · value · listing id). Cluster banner now shows dual first-seen tiles (`First seen (same car overall)` / `First seen (this listing)`). Three info tooltips: Active tile ("X unique cars · Y active listings · Z duplicated"), Sold (window) ("X were deleted, Y were relisted"), Sold (total) (same).
5. **`web/static/index.html`** — added `chartjs-adapter-date-fns@3.0.0` so the Chart.js time scale can parse ISO `recorded_at` strings.
6. **`web/static/style.css`** — `.history-chart` (200px tall canvas frame), `.cluster-dates` (two-card grid for the dual first-seen tiles), themed scrollbars at the bottom: `::-webkit-scrollbar-thumb { background-color: var(--border-strong); border: 2px solid transparent; background-clip: padding-box; }` + slim 8px variant for `.detail-card`, `.filters`, `.thumbs`. Firefox: `scrollbar-color` + `scrollbar-width: thin` on `html`. All references use theme tokens so light mode re-tones automatically.

**Key decisions**:
- Cluster identity becomes the unit of analysis for "is this car sold?" and "how many active cars do we have?" — not raw listings. Raw counts retained alongside truly-deduped counts so the gap can be surfaced in info tooltips rather than hidden.
- `web/analytics.py` gets its own `_NOT_BUYER` copy rather than importing from `web/app.py` (avoids circular). Acceptable duplication: both modules already import from `web/queries.py`; future move can centralize there.
- Chart points are tagged with `listing_id` server-side so the frontend can color them by origin (this listing vs sibling). Visually communicates "this is one car spread across multiple posts" without needing a legend.
- Scrollbars must reference tokens, never hex.

**Mistakes caught**:
- **`analytics.py` silently leaked `Cumpăr` buyer-side listings into every endpoint** — user pointed at the top KPI (86,169) vs model-stats Active (89,635) and asked why. Root cause: `web/app.py:_status_where` filters them globally for `/api/listings`, but `analytics.py` ran raw `WHERE status='active'`. Lesson: every file with SQL against `FROM listings` must replicate the buyer-side filter. Documented as a gotcha in the project wiki + as a decision (`_NOT_BUYER` duplicated by design until a shared SQL-fragment module exists).
- **A round-trip detour into a "minimal navy redesign"** of the whole web UI — user said "make a redesign", I went too far (full Next.js scaffolding plan + 4 dedicated pages + 4 CSS files + page-gated app.js rewrite), they hated it ("just reverse it how it was"). Single `git checkout` + `rm -rf` reverted. Lesson logged in [[../mistakes#scope-creep-on-redesign-requests|mistakes]].
- **Chart.js `parsing: false` blanks time-scale charts** — initially set it thinking it'd speed up rendering; the time scale uses the adapter during parsing, so disabling parsing skips the adapter and the chart shows nothing. Removed the flag.

**Pattern that worked**: every numeric tile now has an `i` info icon attached as the third arg to the `tile(label, val, info)` helper. The pattern means future "where does this number come from?" questions can be answered inline without users having to dig — and matches the existing prank-price tooltip pattern from the prior session.

**Next**: capture daily NBM EUR/MDL + USD/MDL rates so the merged price-history chart can keep each point in its ORIGINAL currency (user requirement) while still displaying a consistent Y-axis. Tracked in [[../todo/999-CarScrapper-todo|todo]].

---

### [2026-05-23 — sell-through tile follow-up]

**What was asked**: a 7th tile in the model-stats card showing the % of cars that sold — user didn't have a name for it ("Active / Sold (window)" rate).

**What was done**: added the **Sell-through** tile in `renderModelStatsCard()` computing `truly_sold_in_window / (active + truly_sold_in_window) × 100`. Tiered display so tiny non-zero rates don't read as 0%. Info tooltip mirrors the cohort framing. Pure client-side — all three inputs already arrive in the existing payload. CSS grid bumped 6 → 7 cols with new breakpoints (≤1400px → 4-up, ≤1100px → 3-up).

**Key decision**: denominator is *cohort-in-window* (active + sold), not lifetime listings or just active. Three other formulas were considered and rejected — see [[../decisions/999-CarScrapper-decisions#2026-05-23-later--sell-through-rate-uses-cohort-in-window-denominator-not-lifetime-listings|the decision log]].

**Pattern**: "rate" metrics over windows generalise to `event_count / (still_open + event_count)`. Reuse this shape if more such tiles get added (e.g. price-drop rate, relisting rate per cohort).

---

### [2026-05-26] KPI auto-refresh with slide animation, "Hide ordered" filter, dealer count query

**What was asked**:
1. Make the KPI stats strip refresh continuously in real-time with a slide-up animation on number changes.
2. Add a filter to hide "La comandă" (cars to order) listings without false-positiving on listings that mention "la comandă" for custom features.
3. Make the model-stats side-card also respect the new filter.
4. Query how many dealers have 100+ cars.

**What was done**:

1. **KPI auto-refresh** — `renderKpis()` in `app.js` now sets a 30s `setInterval`. Tracks previous values per tile in `_kpiPrev`. On each refresh, only tiles whose value changed get re-rendered with a `<span class="kpi-num slide-up">` wrapper. CSS `@keyframes kpiSlideUp` does a 450ms `translateY(100%→0)` ease-out. First paint is instant (no animation). `.kpi-value` gained `overflow: hidden` to clip the animation boundary.

2. **"Hide ordered" filter** — new `hideOrdered` boolean in `state.filters`. Checkbox in the Browse toolbar next to "Deals only". When active, `web/queries.py:build_listing_query` appends `(availability IS NULL OR availability != 'La comandă') AND (offer_type IS NULL OR offer_type != 'Auto la comandă')`. URL-synced via `?hideOrdered=1`. Uses structured fields only — no description parsing, so a listing mentioning "interior la comandă" won't be excluded.

3. **Model-stats card sync** — added the same `hideOrdered` handling to `web/analytics.py:build_extra_filters`. The `model_stats` endpoint in `app.py` already passes all non-stripped params through to `build_extra_filters`, so `hideOrdered` flows automatically. Side-card Active count now matches the grid count when the toggle is on.

4. **Dealer count query** — ran `SELECT seller_name, COUNT(*) ... GROUP BY seller_name HAVING COUNT(*) >= 100` against the live DB. Result: **0 dealers have 100+ active cars**. AGMOTORS leads at 90, TopAuto at 84. Root cause: `seller_id` is NULL for ~98% of listings (534/89,142 have it populated). The scraper's parser doesn't extract the seller profile from detail pages reliably.

**Files modified**: `web/static/style.css` (kpiSlideUp animation + overflow hidden), `web/static/app.js` (renderKpis auto-refresh + _kpiPrev tracking + hideOrdered state/binding/URL-sync), `web/static/index.html` (hideOrdered checkbox), `web/queries.py` (hideOrdered WHERE clause), `web/analytics.py` (hideOrdered in build_extra_filters).

**Key decisions**: see decisions 2026-05-26 — KPI auto-refresh (poll interval vs cache TTL), "Hide ordered" uses structured fields not description parsing.

---

### [2026-05-29] "Scheduler doesn't work, 5th try" — it was 999.md rate-limiting, not a bug

**What was asked**: the auto (999) scraper's scheduler kept failing across ~5 restarts. Logs showed discovery completing (1,144 pages, ~89k listings) then `GET https://999.md/ro/<id> failed after 3 attempts:` with an **empty** error. Later: "doesn't download photos and blocks after 2 listings", "still blocked, yesterday was fine", and a question on whether to just loop `pipeline.py --mode full` instead of the scheduler.

**Diagnosis (all read-only — I changed no code during diagnosis; proven via `git status` = only README.md)**:
- Empty `failed after 3 attempts:` = `httpx.ConnectTimeout('')`. `ping 999.md` replied (ICMP) but `Test-NetConnection :443` failed while google:443 succeeded ⇒ **temporary IP ban** (SYN dropped at edge), not a parser/scheduler bug.
- The ban is **intermittent and rate-based**: a single fetch *and* a 12-concurrent burst from a fresh client both returned <0.5s, and the browser opened the site — so it's volume/behaviour, not a dumb firewall.
- Root cause: the prior "Change Scrapper Logic" commit split into **two simultaneous processes** — `scheduler_f` (sem 12) + `refresher_loop` re-fetching all ~89k detail pages back-to-back (sem 12) = **24 combined**, past 999.md's documented soft-throttle line (~16 → responses 1s→13s) which escalated into bans.
- "0 photos" on listings: parser is fine (fetched listing 78284806 clean → 20 photos, 82761751 → 10). The 0-photos were degraded pages served under throttle (listings logged 1s apart ⇒ photo download wasn't even attempted ⇒ empty photo_urls).
- Later signature changed to `[Errno 11001] getaddrinfo failed` = **DNS exhaustion** under the reconnect storm + asyncio default-executor (DNS) being starved by the parse thread-pool that fast mode hijacked.
- Tick `TIMEOUT after 480s` = a **backlog loop**: ~873 new listings piled up (DB 88,322 active vs ~89,039 feed); full discovery (~240s) + 873 new + verify can't fit in one tick → never drains.

**What was changed** (after explicit user pick "all three fixes", then a correction):
- `scheduler_f.py` — tick **restored to full discovery + verify-sold every 10 min** (user requires 10-min sold detection). My earlier shallow-discovery tick was reverted + the 6h sweep removed.
- `pipeline.py` — fast mode `CDN 32→16`, default executor `24→48` (DNS no longer starves behind parsing); added `_touch_all()` batch-commit every 1,000 rows (fixes `database is locked`); inert `shallow=` param kept.
- `scraper/crawler.py` — inert early-stop params on `discover_all`/`crawl_pages` (unused; `shallow=False` default).
- `refresher_loop.py` — `refresh_older_than_hours=24`, site sem **3**, `fast=False`, pause 5 min.

**Outcome / handed to user**: drain backlog once with `python pipeline.py --mode full` (uncapped, backs up DB), then run `scheduler_f.py` alone; add `refresher_loop.py` (sem 3) only after ticks confirm light. Photos fast again at combined concurrency 15.

**Full runbook**: [[../999-CarScrapper-ratelimit-throttle-dns]].

**Refresher tuning REVERTED (same session, later)**: the incremental `refresh_older_than_hours=24` + sem 3 + `fast=False` change worked *correctly* — on a freshly-synced DB it refreshed 0 (all <24h fresh) and finished a pass in ~1s. But the user read that idle behaviour as broken ("its fucking boken just revert it back") — they want the refresher *continuously* re-fetching every listing for drift, not a 24h gap between touches. `git checkout -- refresher_loop.py` (back to fast=True / sem 12 / all-known / 30s pause) and restored `pipeline.py`'s `skip_discovery` `_touch_all`. **Kept** the non-refresher fixes: scheduler tick = full discovery + verify-sold/10min, and the `cdn=16 / io-threads=48` DNS fix. Live risk re-introduced: scheduler(12)+refresher(12)=24 over the soft-throttle line; documented in the runbook with the `fast=False` middle ground if symptoms return. **Lesson: "refreshes 0 because nothing's stale" is correct but reads as broken to a user who expects constant activity — surface that framing up front, or keep visible progress.**

---

### [2026-05-30] "One of the numbers is wrong" — dedup consistency across the filtering engine

**What was asked**: Two reports, both the same underlying class of bug — a deduped number next to a raw number:
1. Browse side-card showed **508 ACTIVE** for BMW 5 Series PHEV but the year chips below summed to ~67. "Which one is wrong? Fix it for the entire search and filtering engine." Then clarified: the breakdown should be **status-aware** — active cars per year when viewing Active, removed per year when viewing Removed.
2. Make dropdown showed **BMW (10231)** while the grid showed **8,642 listings**. "These should be unique listings only."

**Diagnosis (read-only against live `E:\DB\listings.db` via `mode=ro&immutable=1` — scraper was writing, 806 MB WAL)**:
1. **Nothing was miscalculated.** 508 active (641 raw → deduped) and 67 sold were both correct; the chips were a breakdown of the *sold* set (label literally "Sold by model year"), hardwired regardless of the Active/Removed/All toggle. Sell-through 12% = 67/(508+67) confirmed internal consistency. Root cause: `status` was **stripped** before `model_stats` (`app.py`), so the card never knew the toggle.
2. Dropdown used raw `COUNT(*)`; the grid (`queries.py:90`) collapses each `car_identity` cluster to its newest sibling. Verified deduped BMW active = 8642, exactly the grid.

**What was changed**:
- **Status-aware year breakdown** — `model_stats(status=…)` now computes `year_breakdown` + `year_breakdown_basis` per the toggle: active = newest-active-sibling cluster dedup (`COUNT(*)` per year, sums **exactly** to the Active headline); removed = `_dedup_sql`; all = both summed. `app.py` forwards `status` + folds it into the cache key. `app.js` reads the new fields and relabels heading/tooltip (Active / Sold / Listings by model year).
- **Deduped dropdown counts** — added `app.py:_dedup_where(status)` mirroring the grid's dedup exactly; `list_models` + the `makes` facet now use it. BMW 10231→8642, Mercedes 7887→6803, etc.
- Avoided re-triggering the same confusion: a naive per-year `COUNT(DISTINCT cluster)` gave 511 vs 508 (year-typo clusters double-bucketed) — switched to one-representative-row-per-cluster so it sums exactly.

**Files modified**: `web/analytics.py` (`model_stats` status param + `_active_year_rows`/`_removed_year_rows` + `year_breakdown`), `web/app.py` (`_dedup_where` helper, deduped makes/models, status forwarded to model_stats), `web/static/app.js` (year section uses `year_breakdown`/`_basis`). Verified both sum to headline (508 / 67); `py_compile` clean. Not committed; scraper still writing.

**Pattern / lesson**: every count shown next to the deduped grid must use the *same* per-status cluster-dedup — see the canonical reference [[../999-CarScrapper-dedup-consistency]]. Also: "508 vs 67" wasn't a bug, it was two different metrics adjacent — when a user says "which is wrong", verify against the DB *first* and be willing to answer "neither, here's why" before changing code.

**Decisions**: see decisions 2026-05-30. **Canonical dedup reference**: [[../999-CarScrapper-dedup-consistency]].

---

### [2026-06-05] "YOU SURE ITS WORKING" — recluster_loop liveness + logging fix

**What was asked**: User pasted `recluster_loop.py` output showing `montage pages (0 clusters): 0` on every pass (#1–#3) and challenged whether the daemon was actually doing anything.

**Diagnosis**: It *was* working — the `0 clusters` line is a red herring. The loop runs `relist_v2 --montage 0`, so the montage summary (the file's last `print`, `relist_v2.py:749`) is correctly zero; the real counts (`CLIQUE clusters:` `:658`, `logged N decisions` `:687`) were truncated because the old `_run` only echoed `stdout` last-3-lines, and `apply_clusters`' rebuild summary goes to **loguru→stderr** which the loop printed only on failure. Proven live against `E:\DB\listings.db`: decision-log run `20260605T224751` (= pass #3's `22:47:51`) had 52,338 decisions; `car_identity` = 16,480 clusters / 34,699 listings, ids contiguous 1…16480 (full wipe+rebuild confirmed).

**What was changed**: `recluster_loop.py` only (logging, no behavior change) — `_run` returns the `CompletedProcess`; added `_grep_line`; `one_pass` now surfaces `CLIQUE clusters:` + `logged ` from stdout and `rebuilt ` from `apply_clusters` stderr. `py_compile`/ast-parse clean, needles verified against source. Daemon needs a restart to pick it up.

**Pattern / lesson**: a daemon that "looks dead" in its log may just be logging the wrong signal — verify against DB/state before editing code. loguru defaults to **stderr**; subprocess wrappers that capture only stdout silently swallow it. Full writeup appended to [[../999-CarScrapper-relist-v2-deploy]].

---

### [2026-06-06] "why aren't the primeras shown as relisted?" — tier H (high-overlap merge) shipped

**What was asked**: User screenshot showed 12 identical `Nissan Primera 2002` cards (290 km, €2250, same silver car) not deduped.

**Diagnosis** (decision log + DB): one dealer relisting one car 12×. Only 2 clustered, 10 singletons. All three merge tiers defeated by **self-defeating rarity at scale** — the 12× relist pushed shared-photo freq to 11–13 (>A cap 2), photo dispersion to 2 (>S cap 1), and fingerprint freq to 12 (>B cap 8). The 90% gallery overlap was only a gate, never a merge signal — exactly the deferred "high-overlap path" in [[../999-CarScrapper-relist-v2-deploy]].

**What was changed**: added **tier H** to `scripts/relist_v2.py` (`--high-overlap`, default OFF; merge on ≥5 shared OR ≥60% gallery overlap alone) + a `CHIMERA METRICS` validation line; `recluster_loop.py` now passes `--high-overlap`. Validated full-DB: **+2,190 listings recovered, 0 new year-span≥3 / multi-fuel chimeras, largest cluster unchanged at 26**. Deployed (run `20260606T010429`): Primeras → cluster 973 (11) + 972 (2). User must **restart `recluster_loop.py`** to pick up the daemon flag change (otherwise next pass reverts it).

**Pattern / lesson**: (1) heavily-relisted cars defeat *every* rarity cap — gallery overlap must be a first-class merge tier, not just a gate. (2) **Editing `recluster_loop.py` requires restarting the running daemon**; editing the subprocess scripts it spawns (`relist_v2`/`apply_clusters`) does not. (3) Validate global model changes with chimera deltas (year-span/fuel/largest) before deploying — but those metrics are coarse; the real safety is the ≥5 threshold sitting above bug #3's 2–4 cross-car overlap. Full writeup: [[../999-CarScrapper-relist-v2-deploy]] (tier H section).

---

### [2026-06-06] scheduler_f tick timeout 8min → 6h so a big new-listing backlog finishes in one tick

**What was asked**: "make the scheduler's tick not expire until it has [discovered/detail-fetched] all the cars — it only does ~110 per tick before the tick timeout, but today there were 1200 and it took ages waiting for the timeout." (User clarified the process is `scheduler_f.py` and "renew" = the tick finding/detailing new listings.)

**Diagnosis**: `scheduler_f.py` `JOB_TIMEOUT_SEC["tick"] = 8*60`. The tick (GraphQL discovery + detail-fetch of new IDs + verify-sold) was killed after 8 min having processed ~110 cars; the remaining backlog dripped out ~110 per 10-min fire → hours to clear 1200.

**What was changed**: raised `JOB_TIMEOUT_SEC["tick"]` to `6*60*60` (6h). Safe because the run loop is single-threaded with a file reentrance lock — a long tick just makes the intermediate 10-min `schedule` fires skip (no overlap, no pileup), and the normal cadence resumes once the backlog clears. 6h (not `None`) still kills a genuinely hung job. At the observed ~110/8min rate, 1200 cars finish in ~90 min, well under the cap. Syntax-checked; **daemon needs a restart** to pick it up.

**Pattern / lesson**: a fixed per-job timeout that's shorter than the worst-case backlog turns a scheduler into a slow drip. If a reentrance lock already prevents overlap, the per-tick timeout only needs to bound *hangs*, not *normal long runs* — size it to worst-case work, not to the tick interval. Minor tradeoff noted: during a long blocking tick the hourly WAL checkpoint is deferred until it finishes (WAL can grow), catches up right after.

---

## How to use
After finishing a session on this project, summarize it here.
Focus on: decisions made, mistakes caught, patterns that worked.

[[../projects/999-CarScrapper|Back to 999-CarScrapper]] · [[../index|Vault Index]]
