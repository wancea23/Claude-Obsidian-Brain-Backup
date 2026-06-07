# Past Mistakes & Lessons Learned

> This file tracks mistakes made during AI-assisted development to avoid repeating them.

---

## Session Mistakes Log

### 2026-06-04 — Trusted 64-bit pHash "exact match" as proof of same car; it collides for different cars in the same showroom (999 CarScrapper)
- **Mistake**: Designed a "new" relist algorithm on the premise "≥1 byte-identical (Hamming-0) car photo ⇒ same car". Dry-running it (`scripts/relist_v2.py`) on a 30k batch produced an **85-member Peugeot 3008 "cluster"** — actually ~15 *different* cars chained together. The exact-photo matches were real (Hamming 0) but the photos were **different cars shot in the same AUTOPLAZA.MD showroom from the same angle**: the background dominates the low-frequency DCT, so a 64-bit pHash can't see the car. Two listings with mileage 149,300 vs 158,400 km shared 3 identical phashes, each shared by 8 cars.
- **Why I missed it**: I conflated "identical pHash" with "identical photograph", and assumed dealer photos are unique per car. For fleet dealers they aren't — same lot, same framing ⇒ identical hash. Compounded by **transitive union-find**: one shared template/showroom photo bridges A–B, B–C, … into a fleet-sized chimera even with a ≥2-shared-photo rule (the collisions are also ≥2 per pair).
- **Rule**: pHash (any bit length) measures **composition, not identity** — never let it be the *final* word; it's a candidate generator. A photo is identity-bearing only if it's **rare** (its exact hash appears in ≤2–3 listings). Confirm true "same photograph" with **local-feature matching (ORB/AKAZE + geometric check)**, which rejects different-car-same-angle and survives a blurred plate. Cluster by **cliques, never connected-components**. Validate thresholds on **same-dealer/same-lot** hard negatives, not random pairs (the old thr=10 got "0 FP on 741 random Tucsons" yet fails here). See [[999-CarScrapper-relist-identity-rethink]].

### 2026-06-04 — Built attribute *vetoes* (city/seller/mileage-drop) that would have split a real cross-posted relist (999 CarScrapper)
- **Mistake**: After auditing the live clusters I built a suspicion model that treated **different city + different seller-type + a small mileage drop** as evidence of *different cars* (e.g. for the SM6 pair: Cimișlia/private/160k vs Chișinău/dealer/163k). The user then said the SM6 pair is the **same car**, cross-posted in two cities to reach more buyers. My vetoes would have wrongly *split* a genuine relist, and ~9 % of the "wrong merges" I'd counted (the mileage-drop ones) may include legit cross-posts.
- **Why I missed it**: I assumed a physical car keeps one city/seller/price/mileage. On a classifieds marketplace a relist legitimately moves city, flips private↔dealer framing, re-tests price, and re-types the odometer approximately.
- **Rule**: **Soft attributes are not vetoes.** Identity must be carried by *rare* positive signals (a unique photo, or a rare exact mileage+price), not by penalising metadata differences. When you label data for a precision metric, re-confirm a few "positives" *and* "negatives" with the user before calibrating — I nearly tuned against bad labels. See [[999-CarScrapper-relist-identity-rethink]].

### 2026-05-30 (later) — Re-attacked a DOCUMENTED bug without reading its canonical vault page, then edited the wrong layer (PaleGarden)
- **Mistake**: A fresh chat asked to "fix the fences." I jumped straight in without reading the project's session-start vault pages — even though a dedicated canonical page **`games/PaleGarden/implementation/yard-depth-sorting.md`** already documented this exact open bug (south fences don't occlude Elias), its diagnosis, three hypotheses, and the real fix. I spent the whole session re-deriving it from screenshots: first as a fence **geometry** problem (trimmed a bottom-left stub, added/removed a west edge — all wrong), then finally landed on Y-sort but implemented it by editing **`yard.tscn` directly** (`y_sort_enabled` on root/`Fence`/`BarnFence`, `z_index=5` on trees/barn). That page's header states the invariant in bold: **depth is runtime/script-only in `yard_loop.gd`; `yard.tscn` is NOT modified.** `yard_loop.gd` re-applies its own z-bands at `_ready`, so my tscn edits were **overridden and inert** → "still not fixed." Multiple wrong guesses on the user's hand-painted scene; very frustrating for them.
- **Why I missed it**: I treated "fix the fences" as a cold task and went to the code/screenshots instead of the vault first. I also assumed depth was driven by the scene file (the default) without checking whether a script already owned it — `yard_loop.gd` was right there as a sibling coordinator node.
- **Rule**: At session start, **read the active project's vault pages before touching anything** — especially search `implementation/` for a page matching the task keyword (here "fence"/"depth"/"occlusion" → `yard-depth-sorting.md`). A "player draws on top of / isn't overlapped by X" symptom is almost always **draw-order / Y-sort**, not tile geometry. Before changing how things layer, grep the scripts for who sets `z_index`/`y_sort`/occlusion at runtime (`yard_loop.gd::_setup_building_occlusion`) — if a script owns depth, edit the script, never the `.tscn`. See [[games/PaleGarden/implementation/yard-depth-sorting]].

### 2026-05-30 — Iterated ~12 rounds BLIND on a visual bug because the Godot MCP died + OneDrive served stale code (PaleGarden)
- **Mistake**: While polishing yard depth-sorting/fence occlusion, my Godot MCP connection got replaced mid-session ("Another MCP server connected and replaced this one" — the user's **BLACKBOX** VS Code agent grabbed the single-client godot-mcp socket). I kept editing scripts and asking the user to reload + screenshot, then guessing from stills — for a dozen rounds. Worse, the project lives in **OneDrive**, where Godot frequently fails to detect external file edits, so the user's reloads likely ran **stale code** — meaning several of my "fixes" never executed, yet I kept treating the unchanged result as "the fix didn't work, try another." Hugely frustrating for the user.
- **Why I missed it**: I treated each unchanged screenshot as evidence about my *logic* rather than questioning whether my code was even *running*. I confirmed the MCP was dead but didn't stop and force-resolve the two environment blockers before continuing to ship blind changes. I also kept retrying the dead MCP call hoping it would revive (it can't — needs a fresh session).
- **Rule**: When you **cannot verify** a visual/interactive change (MCP down, can't run, can't screenshot) **and** there's a known **hot-reload reliability risk** (OneDrive/synced folder), STOP after the first failed round and fix the environment first: (1) get a working feedback loop (reconnect MCP via fresh session; close any other MCP client like BLACKBOX — godot-mcp is single-client), (2) move the project off OneDrive so edits load. Don't ship more than ~1 unverifiable change in a row. A debug label that prints a value you set *unconditionally* is the cheapest "is my code even running?" probe — if it doesn't appear, you're stale; stop coding. Godot script reload-on-focus is unreliable on OneDrive; `Project → Reload Current Project` (Don't Save) is the manual force. See [[games/PaleGarden/implementation/yard-depth-sorting]].

### 2026-05-30 — A per-task `asyncio.wait_for` timeout over a semaphore-gated `gather` times out the QUEUE, not the work (999 CarScrapper)
- **Mistake**: To stop a tick freezing, I wrapped each listing worker in `asyncio.wait_for(worker(lid), timeout=120)` and launched all of them with one `asyncio.gather(*...)`. But only `CONCURRENT_REQUESTS` (12) workers can actually fetch at once (site semaphore); `gather` still *starts* all 421 coroutines immediately, so all 421 timeout clocks start at T0. A listing queued 300-deep behind the semaphore burned its entire 120s just **waiting for a slot** and never made a request. At exactly T0+120s the whole backlog (308 listings) timed out **in the same instant**, which tripped the "consecutive failures" circuit breaker and falsely reported a 999.md ban. The site was completely fine — the first 113 listings had succeeded with photos at ~1s each.
- **Why I missed it**: I reasoned about the timeout as "max time to fetch one listing" but `wait_for` measures wall-clock from when the coroutine is *created*, and `gather` creates them all up front. The semaphore queue-wait is inside that window. The dead giveaway in the log was that all 308 timeouts share one timestamp — independent 120s timeouts would smear across 120s, not fire together.
- **Rule**: When you put a timeout on tasks whose concurrency is capped by a semaphore, **acquire the concurrency gate BEFORE starting the timeout clock** (`async with gate: await asyncio.wait_for(work(), t)`), or use a bounded worker-pool so only N coroutines exist at once. Never wrap a fan-out `gather` of more items than the concurrency limit in a per-item `wait_for` — the timeout becomes "time since the batch started", and the tail always trips it. Size the gate slightly above the fetch semaphore so detail+photo phases of different listings overlap. Verified with a 60-task / sem-6 / 0.5s-timeout sim: no-gate timed out 12 of 60; gated finished all 60. See [[999-CarScrapper-ratelimit-throttle-dns]].

### 2026-05-29 — Traded full discovery for a "shallow" tick and silently broke 10-min sold-detection (999 CarScrapper)
- **Mistake**: To stop 999.md rate-banning the scraper, I made the 10-min tick do **shallow discovery** — early-stop after 3 consecutive fully-known GraphQL pages (~6 pages instead of 1,144). It cut request volume beautifully (validated: 6 pages / 3.3s, found new IDs correctly). But a shallow crawl only sees the newest pages, so it **can't compute `missing_ids = known_active − crawled_ids`** — which means **sold/removed detection silently stopped**. I moved sold-detection to a 6h sweep without flagging that as a behaviour change the user might reject. The user did reject it: "we need the sold/removed checked every 10 minutes."
- **Why I missed it**: I optimised for the symptom in front of me (bans from volume) and treated discovery as purely "find new listings", forgetting it's also the input to sold-detection. I didn't restate the job's correctness requirements before changing its scope.
- **Rule**: Before trading completeness for cheapness in a recurring job, enumerate **everything that job's output feeds** (here: full crawl → both new-detection AND sold-detection) and confirm each still holds. When a fix changes *what the job detects* (not just how fast), surface that explicitly and get sign-off — don't bury it. The real fix was volume reduction elsewhere (refresher sem 12→3), not amputating the tick's scope. See [[999-CarScrapper-ratelimit-throttle-dns]].

### 2026-05-29 — Assumed the on-screen building was the `House` node; burned ~6 runs on a mispositioned zone (PaleGarden)
- **Mistake**: Building the house rest zone from `House/HouseWalls`, I assumed the cabin visible at Elias's spawn was the House and that its door sat at the footprint centre. Walked Elias to that cabin repeatedly; the `[E] Rest` prompt never fired. The real `House` was **north, off the spawn screen** (the spawn-visible cabin is a different building), and the door is **right-of-centre and purely decorative** (`HouseWalls` is a solid rectangle — no doorway gap to detect).
- **Why it dragged**: I trusted the visual + the footprint-centre heuristic instead of reading the actual numbers first. Two MCP quirks hid the truth: `mcp__godot__node.get_properties` **can't read runtime-added nodes** (the zone existed per `node.find` but `get_properties` returned NODE_NOT_FOUND — it reads the editor scene, not the running tree), and `get_log_messages` **doesn't capture `print()`**.
- **Rule**: When a procedurally-placed Area2D "doesn't fire", get the coordinates *first*, don't eyeball. Since MCP can't read runtime nodes or `print()`, draw the values into an on-screen `Label` (set the prompt text to `"zone=%s player=%s in=%s"`) and screenshot — one frame tells you position + overlap. And never assume the first building you see is the node you named; verify against `node.get_properties` (position/footprint). When wall geometry has no detectable door, prefer a forgiving full-extent zone over a hardcoded offset.

### 2026-05-28 — Godot MCP `node.update` on running game persists to the scene resource (PaleGarden)
- **Mistake**: While testing collisions on `yard.tscn`, called `mcp__godot__node.update` on `/root/Yard/Elias` to teleport him for verification. The change wrote through to the scene file — next time the game ran, Elias spawned at the test position `(160, 280)` instead of the original `(320, 180)`. User caught it and asked me to revert.
- **Why I missed it**: I assumed `node.update` while the game was running would only affect runtime state (analogous to setting `node.position` in script). It actually modifies the saved scene.
- **Rule**: Treat `mcp__godot__node.update` as **scene authoring**, not runtime poking. To move things only at runtime, attach a debug script and call `Input`-driven movement, or use ScheduleWakeup-style manual play. If you must use it for inspection, snapshot the original values first and restore them.

### 2026-05-28 — `godot --headless --check-only --script <file>` produces false "autoload not declared" errors (PaleGarden)
- **Mistake**: Saw `Parse Error: Identifier "TimeManager" not declared` for `farmhouse.gd` in editor log. Ran `godot --headless --check-only --script scenes/farmhouse/farmhouse.gd` to confirm — got `Identifier not found: GameState`. Almost concluded the file was broken.
- **Why I missed it**: `--script` runs the file as a standalone GDScript, bypassing the project's autoload registration. So every autoload identifier (`GameState`, `TimeManager`, `Constants`, `DayManager`, etc.) reads as undeclared. The real game (where autoloads load) parses farmhouse.gd fine.
- **Rule**: Never use `--script` to validate code that references autoloads. Use `godot --headless --quit` (loads the project, runs `_ready`) or open the project in editor and watch the script tab. The editor's "log_messages" panel can also keep stale parse errors from prior project state — re-trigger a parse before trusting them.

### 2026-05-28 — `INSERT OR REPLACE` + `ON DELETE CASCADE` = silent data loss under concurrent writers (999 CarScrapper)
- **Mistake**: Two pipeline.py processes ran in parallel (scheduler + refresher). Both called `INSERT OR REPLACE INTO listings` for the same new IDs. Listings table has child tables (photos, price_history, listing_features, etc.) all with `ON DELETE CASCADE`. The second writer DELETEd the first writer's row → cascade wiped the photos and history the first writer just built up. Caught only because the user noticed `NEW <id>` lines in the refresher log and asked.
- **Why I missed it**: Reverted my own `skip_discovery` guard when user said "make it act like `pipeline.py --mode full --refresh-known`". Didn't think through what two parallel instances of that command would do to each other.
- **Rule**: Before running two writer processes against the same SQLite DB, audit every UPSERT path for `INSERT OR REPLACE` against tables with `ON DELETE CASCADE` children. Either switch to `INSERT … ON CONFLICT … DO UPDATE` (no delete, no cascade) or guarantee only one writer touches that table.

### 2026-05-28 — Shared SQLite connection per chunk starves other writers (999 CarScrapper)
- **Mistake**: To save per-listing `sqlite3.connect/commit/close` overhead, I shared one connection across all workers in a 2000-listing chunk in `pipeline.py`. Workers don't preempt under asyncio so it was safe for correctness — but the implicit transaction held the SQLite write lock for the full ~17 min chunk duration. WAL mode allows concurrent readers but only one writer; the scheduler's tick waited the 30 s `db.connect(timeout=30)` then died with `database is locked`.
- **Rule**: When sharing a SQLite connection across many ops in a multi-writer system, `conn.commit()` per operation (or every N ≤ a few) so the write lock is released frequently. The connect/close savings (~3-8 min on 89k listings) are not worth blocking other writers. Cost of `conn.commit()` per listing in WAL: ~1-2 ms — negligible compared to the lockout it prevents.

### 2026-05-24 — Index that was unused on sparse data became load-bearing once the column filled in (999 CarScrapper)
- **Mistake**: After backfilling `car_identity_id` from 5.7% → 100% of rows, the web UI hung on "loading..." indefinitely. I had verified clustering worked, dissolved chimeras, even truncated the WAL — but didn't think to check whether existing query plans still held under the new data distribution. The `web/queries.py` cluster-dedup subquery had been "fine" for months because 94% of rows hit the `car_identity_id IS NULL` shortcircuit; once that shortcircuit stopped firing, the subquery fell back to `idx_listings_status_first_seen` and the items query started taking >20s.
- **Fix**: Added `CREATE INDEX idx_listings_car_identity ON listings(car_identity_id, status, first_seen_at)` to schema + live DB. Composite is selected as COVERING INDEX by SQLite, so the subquery never touches the base table. Page load went from hanging → 0.00s.
- **Prevention**: When a feature changes the cardinality / NULL rate of a column that appears in WHERE/JOIN predicates, immediately re-check the query plans of any hot path that touches that column. A "shortcircuit by NULL" optimization silently inverts from "free" to "load-bearing" as soon as the column fills in. EXPLAIN QUERY PLAN of the actual app queries before AND after a backfill is the cheap insurance.

### 2026-05-24 — Forgot Python imports don't auto-reload; long-running daemon held pre-patch module (999 CarScrapper)
- **Mistake**: After patching `db/database.py:find_cluster_for_photos` and `pipeline.py:313` with the template-phash + make+model gate, I told the user to reset and re-run the backfill. The backfill produced clean clusters (78 → 2 mixed-make). But 2 chimeras still appeared, and I couldn't reproduce them by re-running the new function on the offending listings — it returned None correctly. Root cause: the user had a long-running `scheduler.py` / scrape process in another terminal that imported `db.database` BEFORE my patch. Python caches imports per-process; the daemon's in-memory function was the OLD pre-patch code. Concurrent scrapes through that daemon could call the OLD find_cluster_for_photos and form chimeras even while the backfill ran the NEW code.
- **Fix**: (1) Added a defensive runtime guard in `assign_cluster` itself that refuses cross-make/model joins regardless of which `find_cluster_for_photos` was called. (2) Reminder to restart long-running daemons after patching shared modules. (3) Wrote `scripts/dissolve_chimeras.py` to clean up the 2 leftover bad clusters.
- **Prevention**: When patching a module that's imported by a long-running daemon (`scheduler.py`, web app, anything that doesn't restart per invocation), explicitly include "restart the daemon" in the user-facing instructions. AND prefer defensive guards at the lowest-level mutation point (here: `assign_cluster`, which is the actual write) over guards only at the higher-level computation (`find_cluster_for_photos`), so any caller — including stale in-memory ones — can't bypass them.

### 2026-05-24 — Defined "template phash" by absolute frequency, broke legitimate relistings (999 CarScrapper)
- **Mistake**: When designing the template-phash filter to block dealer overlay photos, I first defined a template as "phash appearing in ≥5 distinct listings". Dry-run on the legit Peugeot 3008 ×6 cluster showed every member returning None — the photos used in 5+ relistings of one car got wrongly flagged as templates. The fix would have eliminated the chimeras AND eliminated all genuine multi-relist clusters.
- **Fix**: Redefined template as "phash spanning ≥2 distinct (make, model) values". Information-theoretically clean: a unique car photo can only belong to one make+model; an overlay/placeholder shared across cars always spans ≥2. Dry-run after fix: chimera cid=2892 dissolves (intended); Peugeot 3008 cluster preserved AND extended (the new algorithm found a 7th relisting the broken algorithm missed).
- **Prevention**: When the heuristic for "noise" might collide with a real signal (here: legit re-use of one photo across multiple listings), test the proposed rule against KNOWN-GOOD examples before committing. The dry-run pattern — run new algorithm against the corrupted live DB, check both chimera AND legit cluster behaviour — caught the regression in 30s and cost nothing. Default rule for heuristic filters: pick the dimension that's information-theoretically orthogonal to the legit signal (here: cross-category span, not within-category frequency).

### 2026-05-24 — Almost added a new "specs + seller" rule before checking why pHash wasn't running at all (999 CarScrapper)
- **Mistake**: User asked why 4 obviously-duplicate Toyota Corollas weren't clustering. My first instinct was to propose a new fingerprint signal (seller_id + spec match) on top of pHash. I drafted an `AskUserQuestion` with strictness options before actually checking the DB state. User pushed back: "we have a photos duplication checker program no?". When I finally queried the DB, the real problem was that **97.2% of listings had `car_identity_id IS NULL`** — `pipeline.py:309-326` only clusters when `is_new=True`, so 96k legacy listings never ran through the matcher at all. The fix was a one-shot `--phase cluster` backfill, no new rules needed.
- **Fix**: Queried `SELECT COUNT(*) FROM listings WHERE car_identity_id IS NULL` first. Found 96,326 / 99,054. Then realised the existing pHash matcher was fine — it just never ran on legacy data.
- **Prevention**: When the user says "X isn't working", check that **X is actually executing** before redesigning X. For background/conditional code paths (`if is_new`, hooks, schedulers), the question "is this code running on the rows I'm looking at?" comes BEFORE "is the algorithm right?". A `COUNT(*) WHERE result_column IS NULL` is the cheapest possible diagnostic and answers it in one query.

### 2026-05-24 — Inferred UI intent from one screenshot, built three wrong layouts before asking
- **Mistake**: User asked "modify the SEO for m99gadgets to be findable" and showed one screenshot of the modal they wanted users to land on. I built (1) a standalone Darwin-look third-party landing page, (2) a separate Darwin-skeleton store page with sidebar/breadcrumb/specs, then (3) re-prerendered per-product HTML at `/ro/<cat>/<slug>.html`. Every attempt was rejected with increasing frustration ("WTF did you do, I told you ONLY modify the link"). User actually wanted the existing SPA to serve at clean URLs — NO new pages, NO new layouts.
- **Fix**: Stopped, called AskUserQuestion with three concrete clarifying questions (RU mirror? category-only URL? pushState on modal open?), got crisp answers, then implemented in one shot via Netlify rewrite + `parseRoute`/`pushRoute` in app.js.
- **Prevention**: When user describes a goal ("modify the SEO") and shows a UI screenshot, the screenshot is usually the DESIRED END STATE, not a request to build a new layout that resembles it. Before designing anything, ask: "Do you want me to (a) make the existing UI appear at a new URL, (b) replace the existing UI, or (c) add a parallel UI?". Three small AskUserQuestion options up front beats three full rebuilds.

### 2026-05-24 — `npx serve -s` SPA-rewrites every unknown path, including `/showcase` — broke Hall of Fame locally
- **Mistake**: Used `npx serve static -s -l 8001` to test the new clean-URL routing. The `-s` flag tells `serve` to fall back to `index.html` for any 404, which is what Netlify does for `/ro/*` and `/ru/*`. But `-s` is path-agnostic — it ALSO rewrote `/showcase` (the Hall of Fame directory) and `/showcase/index.html` to the root SPA. User reported "produse populare nu mai merge". Production Netlify was unaffected because `_redirects` is path-specific (`/ro/*` and `/ru/*` only).
- **Fix**: Created `static/serve.json` with explicit `rewrites` only for `/ro/*` and `/ru/*` (mirrors `_redirects`). Removed `-s` from the local invocation. `/showcase/` now serves `static/showcase/index.html` correctly.
- **Prevention**: When the production config (Netlify `_redirects`) is path-scoped, the local dev server config MUST match — don't use the dev server's catch-all SPA flag. Either mirror the rewrites in `serve.json` / `vite.config.ts` / equivalent, or run a tiny custom server (Python http.server / Node http.createServer) with explicit routing logic. The "works in dev, breaks in prod" failure mode is symmetric: also test "works in prod, breaks in dev".

### 2026-05-24 — `spawn("npx", ...)` without `shell: true` → Windows EINVAL on Node 20+ (CVE-2024-27980)
- **Mistake**: Wrote `scripts/prerender.mjs` that spawns `npx serve@latest static -s -l 8765` to run a local server during snapshotting. First attempt: `spawn("npx", args, { shell: platform === 'win32' })` — failed silently in the user's PowerShell. Second attempt: `spawn("npx.cmd", args, { shell: false })` — `Error: spawn EINVAL`. Node 20+ refuses to spawn `.cmd`/`.bat` files without `shell: true` (CVE-2024-27980 hardening against argument injection).
- **Fix**: Replaced the spawn entirely with a 30-line inline `http.createServer` that does its own SPA fallback for `/ro/*` and `/ru/*`. No external process, no shell escaping, no Windows-specific gotchas. Works identically on Windows/macOS/Linux/CI.
- **Prevention**: For build scripts that need a temporary local HTTP server, prefer Node's built-in `http` module over spawning `npx serve` / `python -m http.server` / etc. The dependency surface shrinks AND you control the routing exactly. Spawn external commands only when you genuinely need their behavior (e.g., long-running daemon, complex CLI features). For a static-file-with-rewrites server, ~40 LOC is enough.

### 2026-05-24 — Regex over-stripped indentation in `main()` — `NameError: catalog`
- **Mistake**: While removing the now-dead `write_prerender(catalog, ...)` call from `generate_products.py:main()` via `re.sub(r"\n\s*write_prerender\([^)]*\)\s*", "\n", src)`, the `\s*` swallowed the 4-space indent that preceded the NEXT line (`write_sitemap(catalog, ...)`). The next line ended up at column 0, out of the `main()` function scope. First run: `NameError: name 'catalog' is not defined`.
- **Fix**: Manually re-indented `    write_sitemap(catalog, output["generated_at"])` to 4 spaces. Caught immediately on the first run, took 30 seconds to fix.
- **Prevention**: When using regex to delete a line, anchor on the LINE BOUNDARY not on whitespace runs. `re.sub(r"^[ \t]*write_prerender\([^)]*\)\s*\n", "", src, flags=re.M)` would have left the next line's indent intact. Better: use line-based removal (`[l for l in src.splitlines() if 'write_prerender(' not in l]`). Best: do small surgical edits via the Edit tool instead of regex over an entire file when context whitespace matters.

---

### 2026-05-23 — `aspect-ratio` + `width: 100%` on a grid track with `minmax(0, 1fr)` ballooned the column to the image's natural size
- **Mistake**: To stabilise the photo-modal gallery frame across landscape↔portrait swaps, I set `.main-photo { aspect-ratio: 4/3; width: 100% }` inside a `.detail-card` grid using `grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr)`. The `minmax(0, ...)` track resolves its preferred size from content. With `width: 100%` referencing the track AND `aspect-ratio` deriving height from width, the browser fell back to the img's intrinsic dimensions and the photo column exploded past the modal's `max-width: 1280px`, bleeding photos across the listings grid behind the modal.
- **Fix**: Reverted to height-driven sizing — `.main-photo { width: 100%; height: 100%; max-height: 92vh }` with the img `position: absolute; inset: 0; object-fit: contain`. The frame fills the grid track at whatever width the grid resolves, the image letterboxes inside, and the arrows (positioned against `.main-photo` via `position: relative`) stay pinned across photo swaps.
- **Prevention**: Don't combine `aspect-ratio` with `width: 100%` inside a flexible grid track unless the OTHER axis is also clamped (e.g., `max-height` AND `max-width` BOTH set). With `minmax(0, Xfr)` the track can grow to content, and content with aspect-ratio resolves back to intrinsic. Test in the actual modal at multiple aspect ratios before shipping.

### 2026-05-22 — pHash backfill looped forever on a single corrupt webp (NULL never updated → re-picked every batch)
- **Mistake**: `_phash_for` returned `None` on unhashable files; the batch loop only appended successful updates (`if h is not None: updates.append(...)`). Combined with `WHERE phash IS NULL ORDER BY listing_id LIMIT 2000`, the same corrupt row (`81135709/11.webp`, 0 bytes from a truncated download) sat at the front of the queue every batch and reappeared forever. Visible as a `phash failed for ...` warning every ~80 seconds for 8+ hours.
- **Fix**: Introduced `PHASH_FAILED = -1` sentinel (bit-pattern all-ones, statistically impossible as a real phash). Write the sentinel when phash fails — file missing, zero bytes, or `imagehash.phash` raised. Exclude it from `find_cluster_for_photos` queries on both sides. Patched live with `UPDATE photos SET phash=-1 WHERE id=?` so the running scraper picked up the fix on next batch without restart (WAL mode).
- **Prevention**: When a backfill query is `WHERE col IS NULL` and the row-producing step can fail, **always write something on failure** — a sentinel, a flag column, anything but NULL. Otherwise the failing row gets infinite retries and (worse) blocks forward progress depending on the sort order. Pre-stamp known-bad rows at the start of a long job (we swept all zero-byte files in one pass).

### 2026-05-22 — `executescript(schema.sql)` aborts when schema references a column the existing DB doesn't have yet
- **Mistake**: Added `CREATE INDEX IF NOT EXISTS idx_photos_phash ON photos(phash);` to `db/schema.sql` and a corresponding `ALTER TABLE photos ADD COLUMN phash INTEGER` migration in `init_db`. On the existing DB (which pre-dates the phash column), `init_db` ran `conn.executescript(schema)` FIRST, hit the index DDL referencing a missing column, and aborted the whole script with `OperationalError: no such column: phash` before reaching the migrations. The user got the error on `python -m scripts.backfill_phash --phase all`.
- **Fix**: Reordered `init_db` to run the additive `ALTER TABLE` block FIRST, then `executescript`. Both blocks are tolerant of repetition (`ADD COLUMN` raises `OperationalError` on existing columns → ignored; `CREATE IF NOT EXISTS` is a no-op on existing objects). On a fresh DB the ALTERs silently fail (no parent table yet), executescript creates everything from the canonical schema, no harm.
- **Prevention**: When schema.sql evolves to reference columns added in additive migrations, ALWAYS run migrations before executescript. The pattern generalises to indexes, triggers, views, generated columns — anything that touches a column. If you add a column AND an index/trigger on that column in the same migration, do the column-add first.

### 2026-05-22 — `imagehash.phash` returns unsigned 64-bit; SQLite INTEGER is signed (silent overflow on insert)
- **Mistake**: Stored `int(str(imagehash.phash(img)), 16)` directly to SQLite. ~50% of phash values exceed `2**63-1`. Backfill blew up mid-run after ~hashing all 1.14 M photos: `OverflowError: Python int too large to convert to SQLite INTEGER` on the batched `UPDATE photos SET phash = ?`.
- **Fix**: Wrap at the boundary: `if u >= (1 << 63): u -= (1 << 64)`. The Hamming-distance helper already masks XOR back to 64 bits (`& ((1 << 64) - 1)`), so signed/unsigned representation doesn't affect comparisons.
- **Prevention**: SQLite INTEGER ≤ 2^63-1. Any time you store an unsigned 64-bit hash, ID, or epoch-nanosecond, wrap to signed at the boundary OR store as TEXT/BLOB. XOR/AND/OR bitwise ops are bit-identical between signed and unsigned, so Hamming/equality checks need no other change.

### 2026-05-22 — Status toggle didn't flip `has_user_filters`, so Removed-tab pagination used the cached ACTIVE count
- **Mistake**: `web/queries.py:build_listing_query` set `has_user_filters = True` for equality, range, multi-select, and free-text filters — but treated the `status` param as a no-op for that flag. `web/app.py:/api/listings` checked the flag to decide whether to run a real `COUNT(*)` or reuse a 60s-cached active-count. When the user toggled to Removed, the cached "89,773 active" count was still used for pagination → UI rendered 3,400+ pages, most empty (only ~6,861 rows actually existed).
- **Fix**: Set `has_user_filters = True` when status is `sold`, `removed`, or `all`.
- **Prevention**: Any flag that gates "is this the default query / can we use a cached count" must be flipped by EVERY narrowing filter — including ones that look like simple state toggles. Test: would the COUNT change between the toggle's positions? If yes, the toggle is a filter.

### 2026-05-22 — Used CSS variables that don't exist in the project; component looked broken in dark mode
- **Mistake**: Wrote new component CSS referencing `--card`, `--divider`, `--bg-elevated`. None of those tokens are defined in this project's `:root` blocks. CSS `var(--foo, fallback)` fell through to literal-hex fallbacks that almost matched the dark theme but lacked the proper border/elevation contrast. Year chips dissolved into a single run-on string ("2007 · 32008 · 5…"); 6 stat tiles read as 6 separate boxes instead of one composed surface.
- **Fix**: Rebuilt the whole card against the project's actual tokens (`--surface`, `--surface-2`, `--surface-3`, `--border`, `--text`, `--text-soft`, `--text-faint`, `--accent`, `--accent-soft`, `--accent-border`).
- **Prevention**: Before writing any new component CSS, GREP existing `style.css` for `--*` definitions. Never invent token names. If the design needs a token that doesn't exist, add it to `:root` (light + dark variants) FIRST, then reference it. Tokens are the contract.

### 2026-05-19 (late) — Defaulting class init args from a mutable config silently broke `--fast`
- **Mistake**: `Session(site_concurrency: int = config.CONCURRENT_REQUESTS)` looked clean but Python evaluates default arg values once, at function-definition time (i.e. when the class block executes during import). The pipeline's `--fast` mutation `config.CONCURRENT_REQUESTS = 16` happened at runtime AFTER the class was defined, so every `Session()` call still used the import-time value of 8. The user's "it's not fast at all" complaint came from this.
- **Symptom**: --fast appeared to do nothing. Throughput was identical to default.
- **Fix**: Read `config.CONCURRENT_REQUESTS` inside `__init__` body, not as a default arg. Pass `None` as the parameter default and resolve from config at construction time.
- **Prevention**: For any class/function meant to pick up CLI-mutated config values, the rule is: **default args are import-time, config reads must be runtime.** Treat `def fn(x=config.SOMETHING)` as a bug whenever `SOMETHING` could be mutated.

### 2026-05-19 (late) — A global `asyncio.Lock` quietly serialized 16 concurrent workers down to 1
- **Mistake**: To make stats counter increments and log emits "safe", the pipeline wrapped the entire post-fetch worker body in `async with sem_lock:`. With `asyncio.gather` spawning 500 workers and 16 concurrent in-flight network calls, only 1 could be in the DB+log block at a time. Effective throughput collapsed to single-worker speed.
- **Symptom**: 2.7 listings/s observed despite sem=16 supposedly active. Workers spent most of their time queued behind each other.
- **Fix**: Removed the lock entirely. CPython dict updates are atomic under the GIL (`stats["x"] += 1` is fine). SQLite WAL handles its own writer serialization (briefly) at the engine level. Logger calls are thread-safe.
- **Prevention**: Before adding any global lock in async code, ask "what specifically needs protecting?" If the answer is "atomic dict updates" or "writer serialization of something that already serializes itself", you don't need a lock. Locks that span both I/O and CPU work serialize everything inside.

### 2026-05-19 (late) — Trusting ML on uncleaned inputs produced hallucinated "deals"
- **Mistake**: Trained the fair-price model on 407 archived listings — looked fine: R² 0.86, MAE €2,554. But the top deals it surfaced were all seller typos (10-million-km Mitsubishi, €1,111,111 Mercedes). Listings with absurd mileage hit the prediction clamp at the model's upper bound, producing -100% "deal" flags. The model wasn't lying; it was correctly extrapolating from garbage. The user immediately spotted this with "where did you take these prices?"
- **Symptom**: Hot-deals feed looked impressive (huge -90% discounts) but every entry was an obviously broken listing.
- **Fix**: Apply the same sanity filter at BOTH training AND inference: `year IS NOT NULL AND year BETWEEN 1980-2030 AND mileage_km BETWEEN 1000-500000 AND price_eur BETWEEN 500-200000`. Also clamp `delta_pct > -90 AND < 500` for the flag classification so listings that hit prediction clamps can't become "deals".
- **Prevention**: When deploying an ML model on noisy real-world data, the inference-time filter is at least as important as the training-time filter. A row that would distort training will also produce a wrong prediction at scoring time. Reject at both ends — and surface filtered-out listings as "unranked", not "amazing deals".

### 2026-05-19 (late) — Assumed parallelism helps without measuring the bottleneck
- **Mistake**: Built `--shard N/M` for parallel scraping, told the user "4 shards = ~4× speedup". User ran 4 shards, one got 429'd, total throughput stayed flat.
- **Root cause**: 999.md rate-limits per IP. N shards from one IP just split the same throttled pipe N ways. AND each shard independently re-runs the full GraphQL discovery (1,130 pages × 4 = 4× the load), making the rate-limit case worse.
- **Symptom**: No speedup. One shard crashed.
- **Fix**: Recommended `--fast` (single fast process) as the primary path. Documented in `--shard` help text that sharding is only useful with multiple IPs/auth tokens. Added manifest-based discovery sharing to at least reduce the duplicated-discovery waste for users who do shard.
- **Prevention**: Before adding parallelism for "speed", identify where time is actually spent. If the bottleneck is a third-party server (rate limit, slow response), more local processes don't help — they often hurt. Benchmark first; parallelize only when local resources are saturated.

### 2026-05-19 — 999 CarScrapper: destructive delete in "verify_sold" cost the user 235 listings
- **Mistake**: A function named `delete_listing(conn, lid)` inside `scripts/verify_sold.py` was — name notwithstanding — actually destructive: `DELETE FROM listings`, `DELETE FROM photos/price_history/...`, and `shutil.rmtree(photo_dir)`. The pipeline called it for every listing whose 999.md detail page returned "Anunțul nu a fost găsit". The user thought "sold/removed" meant a soft-archive (it was labelled that way in the UI) and only noticed when a sweep logged `listings_deleted=235`. Of 9 surviving orphan photo folders, all were empty shells (rmtree had succeeded); 999.md returned "not found" for all 9 — fully unrecoverable from local sources.
- **Root cause**: a function with a destructive verb in its name + a confidently-named "verify" file led to a confidently-named action that didn't match the semantic the rest of the system was suggesting (UI already said "Removed", not "Deleted"). No backup, no audit trail of which IDs were destroyed.
- **Fix**: rewrote `delete_listing` to soft-archive (`status='removed'`, `removed_at=now`, photos preserved). Added `scripts/backup_db.py` (SQLite online-backup, keeps last 14) + auto-runs at the start of every `--mode full` pipeline so even a future bug has a same-day rollback. Pipeline now logs the list of archived IDs in each run for audit.
- **Prevention** — apply broadly:
  1. **Never destroy data without an explicit, separate, auditable trigger.** If the system says "removed", it should *flag*, not destroy.
  2. **Hot-backup before any destructive op** — even if you "know" it's safe. `sqlite3 conn.backup()` to a dated file is ~60s and gives a same-day rollback for free.
  3. **Function names should match the irreversibility of the action**. `delete_listing` should not be a `sync` step; if the name reads as destructive, it must be wired through an explicit confirmation path.
  4. **Log the IDs of anything that gets removed/archived/etc.** Counts aren't enough — when the user asks "which 235?" the answer can't be "I don't know".
- **General lesson**: when extending a system, audit every action whose name implies state change. Skim every `DELETE`, `rmtree`, `truncate`, `force-push`, `--no-verify` you see in a path that gets called automatically.

### 2026-04-19 — graphify setup
- **Mistake**: graphify `update` command fails with `Permission denied: *.tmp` if a previous run was interrupted mid-write
- **Fix**: Delete stale `.tmp` files in `graphify-out/cache/` before retrying
- **Prevention**: Always check for `.tmp` files if graphify fails on rerun

- **Mistake**: `graphify --version` is not a valid command (returns error)
- **Use instead**: `graphify --help`

- **Mistake**: graphify installs to a path not on $PATH on Windows (Python user scripts dir)
- **Fix**: Export `PATH` with the Scripts dir before running graphify in bash
- **Path**: `C:/Users/SURFACE/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/LocalCache/local-packages/Python313/Scripts`

---

## General AI Assistance Mistakes

### Over-engineering
- Do not add extra features, refactoring, or "improvements" beyond what was asked
- A bug fix should not include code cleanup
- No docstrings/comments on untouched code

### File Management
- Never save working/temp files to the root folder (use `/src`, `/tests`, etc.)
- Never create README or docs files unless explicitly asked

### Parallel Work
- All related operations must be in ONE message (batch reads/writes/edits)
- Do not check agent status after spawning — wait for results

---

## Project-Specific Mistakes

### m99gadgets — CSS `position:fixed` with both `top` and `bottom` set
- **Mistake**: Set `position:fixed; top:12px; right:1.5rem` on `.cart-btn` base style (for desktop overlay), then set `bottom:74px` in the `@media(max-width:640px)` block without unsetting `top`. When both `top` AND `bottom` are set on a `position:fixed` element, the browser stretches the element to fill the gap between them → cart became a full-height bar.
- **Fix**: Add `top: auto` in the mobile rule to reset the base `top` value
- **Prevention**: Any time a mobile override changes `bottom` on a fixed element, always also set `top: auto` (and vice versa)

### m99gadgets — SEO canonical pointed at a domain the user didn't own
- **Mistake**: Site shipped with `<link rel="canonical" href="https://m99gadgets.com/...">` on every page + sitemap/OG/JSON-LD all referencing `m99gadgets.com`. User actually owns `m99gadgets.app`. Google read the canonical, tried to index `.com`, failed → nothing got indexed. User spent days wondering why "SEO doesn't work".
- **Fix**: Grep-replace `m99gadgets.com` → `m99gadgets.app` across the whole project tree (67 files, 1,479 replacements). Includes `generate_products.py:59` so future regenerations stay correct.
- **Prevention**: After setting up a production domain, always `grep -rn <old-or-placeholder-domain>` across the repo. Canonical tag is authoritative for Google — a wrong canonical is worse than no canonical.

### m99gadgets — "Netlify DNS propagating..." label doesn't mean DNS is actually configured
- **Mistake**: User saw "Netlify DNS propagating..." in the Netlify UI and assumed everything was set up correctly, waited >24h for it to finish. Netlify shows that label the moment you add a custom domain, regardless of whether the registrar's nameservers have been switched. In this case, nameservers at name.com were still `ns1-4.name.com` (defaults), so Netlify was waiting for a change that never happened.
- **Fix**: At the registrar (name.com), replace the 4 default NS entries with the 4 Netlify-provided `dns1-4.pXX.nsone.net` entries shown in Netlify's DNS panel.
- **Prevention**: Before trusting Netlify's "propagating..." label, verify with `nslookup -type=ns <domain> 1.1.1.1`. If it returns `*.nsone.net` → DNS is correctly switched. If it returns registrar defaults (`*.name.com`, `*.namecheap.com`, etc.) → NS swap was never done at the registrar.

### m99gadgets — Safari iOS `position:fixed` inside `backdrop-filter` parent
- **Mistake**: Left cart button inside `<header>` which has `backdrop-filter: blur(20px)`. On Safari iOS, `position:fixed` children of a `backdrop-filter` ancestor get positioned relative to that element instead of the viewport → cart button invisible/misplaced on mobile Safari.
- **Fix**: Move any `position:fixed` UI element to be a direct child of `<body>`, outside the `backdrop-filter` parent
- **Prevention**: Never put `position:fixed` elements inside elements that have `backdrop-filter`, `transform`, `filter`, or `will-change: transform`

### 999 CarScrapper — Assumed list page was server-rendered; got an empty SPA shell
- **Mistake**: Wrote an HTML crawler for `999.md/ro/list/transport/cars?page=N` assuming server-rendered listing IDs. `httpx` returned 700 KB of HTML with zero IDs. First test run reported "no listings" and exited. Site is Next.js — listing data streams in client-side after hydration.
- **Fix**: Captured `POST /graphql` traffic in agent-browser, identified the `SearchAds` operation (subCategoryId 659 for cars, pagination `{limit: 78, skip: N*78}`), rewrote crawler to hit that endpoint directly. The endpoint also returns `count` so the crawler stops at the real end instead of probing for empties.
- **Prevention**: Before scraping any modern site, fetch the URL with plain `httpx` and grep for one expected value (a listing ID, a price, a known string). Zero hits = SPA → open the network tab, find the XHR/GraphQL call, hit that instead. Pagination on these is usually `{limit, skip}` not `?page=N`.

### 999 CarScrapper — Partial-match selectors swallowed an entire `<script>` payload
- **Mistake**: `BeautifulSoup.find(string=re.compile("Localitate"))` matched the substring "Localitate" inside a Next.js i18n JSON bundle living in a `<script>` tag. `el.parent.get_text()` then returned the whole 30 KB JSON dump, which got stored as the `location` field for 1,706 of 1,709 listings. UI showed pages of `self.__next_f.push([1,"...")` garbage where the city should be.
- **Fix**: 1) Specific selector — `div[class*="map__address"]` (verified in agent-browser DOM). 2) Length/content guard via `_looks_like_script()`. 3) Defence-in-depth: `parse_listing()` now calls `soup(["script","style","noscript","template"]).decompose()` as the very first step so no extractor can EVER see script content. 4) Cleared the bad column with one UPDATE + kicked off `--refresh-known`.
- **Prevention**: Whenever you use `find(string=…)`, `[class*="…"]`, or any partial match in BeautifulSoup — decompose `<script>`, `<style>`, `<noscript>`, `<template>` FIRST. Even when you think the selector is specific, Next.js / Nuxt / Remix sites embed massive JSON blobs in script tags and your "Localitate" match will hit i18n keys.

### 999 CarScrapper — Async photo downloads were sequential per listing
- **Mistake**: `for url in photo_urls: await session.get(url)` inside `save_photos`. With 10 photos × ~700 ms polite delay = ~7 s of pure I/O per listing, even though those photos are independent and could fetch concurrently.
- **Fix**: `asyncio.gather(*[_fetch_and_save(...) for url in urls])`. Combined with per-host semaphores (small for site, large for CDN) and `asyncio.to_thread` for the Pillow encode, took a 2-page test from 8.5 min → 70 s (7.2× faster).
- **Prevention**: If a code path `await`s in a loop and the iterations are independent, it almost always wants `asyncio.gather`. Concurrency is bounded by the semaphore, not by the loop. Also: any sync CPU work (Pillow, lxml, deep JSON) inside async handlers belongs in `asyncio.to_thread`.

### 999 CarScrapper — Single global semaphore throttled CDN to site rate
- **Mistake**: One `asyncio.Semaphore(5)` in `session.py` covered both `999.md` HTML requests and `i.simpalsmedia.com` image requests. The CDN can absorb 30+ concurrent connections, but it was sharing 5 slots with the polite-rate site fetches. Also: the 300–800 ms politeness jitter applied to CDN requests too, which is pointless.
- **Fix**: Two pools — `_site_sem` (8, polite delay) and `_cdn_sem` (32, ~0 ms delay). Route by `urllib.parse.urlparse(url).hostname`. Static-asset CDNs are built to handle bursts; treating them politely is wasted budget.
- **Prevention**: When a scraper hits multiple hosts, separate rate limits per host. The same call to `session.get(url)` should pick the right pool based on the URL's hostname, not force the caller to know which pool to use.

### 999 CarScrapper — CSS `display: grid` on a modal overrode HTML `hidden` attribute → UI frozen
- **Mistake**: `.detail` modal had `display: grid; place-items: center` for centering. The user-agent stylesheet sets `[hidden] { display: none }` but my custom `display: grid` had higher specificity and won. Result: setting `el.hidden = true` left the dark overlay visible and intercepting every click. Whole page looked frozen.
- **Fix**: Added `[hidden] { display: none !important; }` early in `style.css`. Now the hidden attribute ALWAYS wins regardless of any later `display:` rule.
- **Prevention**: Any project that toggles state with the HTML `hidden` attribute should drop `[hidden] { display: none !important }` at the top of its stylesheet. The user-agent default is too weak to compete with any author-specified `display:` rule.

### 999 CarScrapper — Detected "expirat" by substring match against `<script>` content
- **Mistake**: Tried to verify "is this listing actually gone?" by `if 'expirat' in r.text.lower()`. Got 4/4 true positives in a probe and concluded the scraper was right. But "expirat" was matching the i18n KEY `"ad_expired":"Anunțul este expirat."` inside the `__next_f.push` JSON in a `<script>` tag — present on EVERY listing page regardless of state. Detection was a coin flip dressed up as proof.
- **Fix**: Strip `<script>/<style>/<noscript>/<template>` first, then read `soup.get_text()` and look for the actual visible "Anunțul nu a fost găsit" page text. Codified in `scripts/verify_sold.py:page_state()`.
- **Prevention**: NEVER substring-match against raw HTML on a JS-framework site. The i18n bundle, error message catalog, validation messages, etc. all live in `<script>` tags. Always decompose script tags first, OR query specific DOM elements, OR check for very-unlikely-to-collide strings.

### 999 CarScrapper — Diff-and-delete logic without verification = false-positive sold flags
- **Mistake**: Pipeline marked any listing missing from the latest GraphQL discovery as `status='sold'`. But 999.md's discovery occasionally drops listings that are still alive (paused, hidden-from-feed, premium-only inventory). 3 of 4 of my sold-marked listings still had perfectly fine listing pages with full specs.
- **Fix**: Verify each newly-missing ID by fetching its URL. Three outcomes: deleted-page → DELETE row + photos; spec-page-present → revert to active (false positive); other → mark sold. Same logic baked into `pipeline.py` and the standalone `scripts/verify_sold.py`.
- **Prevention**: Any "compute set difference, then act destructively" workflow should verify each diff item against the source of truth before acting. The cost is N HTTP calls per sweep, but N is small (only newly-missing rows). Anti-pattern: trusting one API call as the only source for "this no longer exists".

### 999 CarScrapper — Wrapper-class selector matched main + old + installment prices together
- **Mistake**: `soup.select_one('[class*="price"]')` matched the WRAPPING div `styles_price__section__uBgxS` that contained 4 separate price-related children: main price (15,990 €), crossed-out old price (19,000 €), discount (-16%), AND "Prima rată: 100 €" (installment for credit deals). `get_text()` concatenated them; the regex grabbed the FIRST `<num> €` it saw — often the 100 € down-payment instead of the real price. 191 listings ended up with prices <500 € (most at 1 €).
- **Fix**: Inspect DOM with agent-browser to find specific child selectors. Use `[class*="price__main"]` for the current price and `[class*="oldprice__value"]` for the crossed-out discount. Added `old_price_eur` and `old_price_mdl` columns via live `ALTER TABLE`. Nulled bad rows so the refresh-known pass repopulates them.
- **Prevention**: If `getText()` of your match returns more than one piece of data, the selector is too broad. CSS modules with `styles_<group>__<piece>__<hash>` patterns are particularly trap-laden — the parent class name appears as a prefix on every child. Always select the leaf, not the wrapper. Test in DOM, not on intuition.

### 999 CarScrapper — Editing parser code didn't fix the running scraper (Python caches imports)
- **Mistake**: Fixed the price-parsing bug in `scraper/parser.py`, expected the running background `--refresh-known` job to pick up the fix. It didn't — Python imports a module once per process and caches it. The 13 GB background scraper kept writing bad prices for ~10 minutes while I was checking the DB.
- **Fix**: Kill the running process (`taskkill /PID <id> /F`), then start a fresh one which imports the updated module.
- **Prevention**: Whenever you edit code that's being executed by a long-running background process, you MUST restart that process for the change to take effect. There's no hot-reload unless you set it up explicitly (uvicorn `--reload` only watches its own Python files). For long-running scrapers, factor that restart cost into the fix.

### 999 CarScrapper — `asyncio.gather(*tasks)` over 80k coroutines pinned ~13 GB RSS
- **Mistake**: Pipeline did `tasks = [worker(lid, ...) for lid in scrape_targets]; await asyncio.gather(*tasks)` for the entire scrape set (~80k items on a full crawl). All 80k coroutines, their Futures, and the long-running httpx connection pool stayed live for the ~10 h run. RSS grew monotonically to 13 GB by end. No headroom on smaller machines, OOM risk.
- **Fix**: Process in chunks of `SCRAPE_CHUNK_SIZE = 500` (added to `config.py`). Each chunk uses a fresh `async with Session()`, full gather over just those 500, then context exit tears down the httpx pool and `gc.collect()` releases parse trees / photo bytes. Logs per-chunk RSS via `psutil` (optional dep) so growth is visible. Result: RSS stable at a few hundred MB across the run.
- **Prevention**: `asyncio.gather` is fine for hundreds of tasks, not for tens of thousands — every coroutine + its Future stays in memory until the whole gather resolves. Above ~10k tasks, OR if any task transiently allocates >1 MB, chunk + recycle. Use `async with Client()` per chunk (not a single shared client) so the connection pool genuinely resets between batches.

### 999 CarScrapper — Refresh-path silent NULL overwrite on mid-run deletions
- **Mistake**: A listing deleted on 999.md between discovery and the per-listing detail fetch (later in the SAME run, sometimes hours later) returned the "Anunțul nu a fost găsit" page. `parse_listing` dutifully produced a dict with all `None`s for car identity and price. `update_listing` then UPDATE'd the row, overwriting real `price_eur`, `mileage_km`, `make`/`model`, etc. with `NULL`. Listing stayed `status='active'`. Symptom in the log was the now-iconic `[N/M] upd <id> ? ?y ?€ (0 photos)` — the `?` came from `data.get('make') or '?'` placeholders.
- **Fix**: Added `_is_stub(data)` in `pipeline.py` worker. On refresh, a stub triggers `scripts.verify_sold.delete_listing` (soft-archive: status='removed', removed_at=now, photos+history kept) instead of UPDATE. Logged as `DEL <id> (deleted mid-run)`. On NEW, stub just increments `errors` and skips insert. Existing rows with NULLs from the bug can be recovered next tick via verify-missing (now enabled in tick mode too) or via `scripts/verify_sold.py`.
- **Prevention**: When parsing a third-party page, define an explicit "stub shape" predicate per source (= what does the source return when the entity doesn't exist?). Branch stubs into the deletion path, never into the UPDATE path. NULL-on-UPDATE is destructive: there's no undo without restoring from backup. Better to drop the write than to silently corrupt the row.

### 999 CarScrapper — `scrape_runs` rows orphaned in `status='running'` after Ctrl+C
- **Mistake**: `start_run` inserts `status='running'`; `finish_run` updates it on clean exit. If `pipeline.py` is killed (Ctrl+C, terminal close, OS kill), the UPDATE never fires and the row stays `running` forever. Three orphans accumulated during testing.
- **Fix**: (TODO — see todo file) Add a startup sweep that marks any pre-existing `status='running'` rows as `failed` before starting a new run. Cosmetic only, but it skews the stats endpoint.
- **Prevention**: Whenever a long-running task writes a "started" row and updates it on completion, add a startup recovery step that handles orphans from prior crashes. Same applies to lock files, PID files, anywhere a "begin/end" pair can be interrupted.

---

## Scope creep on "redesign" requests (2026-05-23)
- **Where**: `999 CarScrapper/web/static/` — user asked to "create a new design", I went all the way to a full Next.js scaffolding plan + 4 dedicated pages (`/`, `/analytics`, `/ml`, `/favorites`) + 4 modular CSS files + page-gated `app.js` rewrite + new backend routes serving them. User had to say "just reverse it how it was" and the whole thing reverted via `git checkout` + `rm -rf`.
- **Why it happened**: jumped to "full redesign" framing without anchoring on what the user actually had. The current app is a single-page vanilla-JS UI with tab switching — "redesign" in that context = restyle existing components, not split architecture into multiple pages and change the framework. AskUserQuestion went too broad ("which palette? which stack?") instead of narrow ("what specifically don't you like about the current look?").
- **Prevention**:
  1. Before any "redesign" task, dump the current UI's structure first (read `index.html`, list tabs/sections) and confirm with the user: "you want me to restyle these N components, right?" — not "what stack should we use?"
  2. Default to in-place restyles. Only propose architectural changes (page splits, framework migrations) if the user explicitly asks for "rebuild" or "rewrite."
  3. When a user picks "minimalist" or "navy dark" in a style question, that's a *palette* answer, not permission to also re-architect.
  4. Stage redesigns: ship the palette change first as a single commit, then iterate. Don't combine "restyle" with "restructure" in one go.

---

## m99gadgets — deleting "duplicate" image originals scrambled photo order + 404'd the showcase (2026-06-06)
- **Mistake**: To kill webp duplicates I deleted 176 jpg/png originals that all had `.webp` twins. Two things referenced those files **by exact name**: (1) `products_manual.json` encoded each product's curated photo order with the ORIGINAL extension for early photos (`name.png`) and `.webp` for later ones; the build's `existing_manual_images` filter dropped the now-missing `.png` entries, and `os.listdir()` re-appended their webp twins at the end in arbitrary order → main photo landed mid-gallery for 31 products. (2) `static/showcase/index.html` (Hall of Fame) hardcoded `hof/*.png` (6 refs) → broken images on the live page.
- **Fix**: build now remaps a missing original to its `.webp` twin **in the same position**; restored the 31 scrambled orders from `git show HEAD:static/data/products_manual.json` (map names → webp); switched the 6 showcase refs to `.webp`. Verified 0 non-webp refs / 0 gallery dups / order matches git.
- **Prevention**: before deleting any file, **grep the repo for hardcoded references to its exact name** (HTML/JS/JSON manifests, not just the generator). When an ordered list is keyed by filename, mutate it position-preserving — never drop-and-reappend, and never let `os.listdir()` order define a user-facing sequence. Store ordered manifests with the canonical (post-conversion) extension so a later cleanup can't invalidate them.

---

## AI-Girl — Python 3.13 venv for ai-toolkit = wheel hell (2026-06-07)
- **Mistake**: Built the ai-toolkit training venv on the system **Python 3.13**. Two installs failed mid-way:
  `scipy==1.12.0` (no cp313 wheel → tried to compile, no Fortran compiler), then `numpy` (pulled <2.1 via
  librosa→numba, no cp313 wheel → source build → `ld` errors). Burned a full torch download (2.8 GB) twice.
- **Fix**: Rebuilt the venv on **Python 3.12** (`py -3.12 -m venv venv`) — cp312 wheels exist for the whole
  stack. Also bumped `scipy==1.12.0`→`>=1.14.1`. Install then went clean.
- **Prevention**: For ML training stacks (kohya, ai-toolkit, diffusers-from-git), **use the README's
  recommended Python (here 3.12), not the newest installed**. Bleeding-edge 3.13/3.14 routinely lacks wheels
  for scipy/numpy/numba/bitsandbytes → silent source builds that fail on Windows without a compiler. Check
  `py -0p` for an older interpreter before creating the venv. See [[ai-girl-lora-training-local|Training Runbook]].

---

## How to Use
- Before starting a task on a project, check this file for known pitfalls
- After a mistake is identified, add it here immediately
- Cross-reference with [[preferences]] for what to do instead
