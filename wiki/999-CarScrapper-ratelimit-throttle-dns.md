# 999 CarScrapper — Rate-limit, Soft-throttle & DNS Exhaustion (runbook)

> Deep-dive from the 2026-05-29 session where "the scheduler doesn't work (5th try)".
> Every symptom traced back to **request volume**, not a code bug. Read this before
> touching scheduler/refresher concurrency or blaming the parser.
> Related: [[decisions/999-CarScrapper-decisions]] · [[todo/999-CarScrapper-todo]] · [[projects/999-CarScrapper]]

---

## The three failure signatures (and how to read them)

999.md defends itself in escalating layers. Same root cause (too many requests), different log signature depending on severity:

| Log line | What it actually is | Test that confirms it |
|----------|--------------------|----------------------|
| `GET ... failed after 3 attempts: ` *(empty after colon)* | `httpx.ConnectTimeout('')` — TCP SYN to `:443` dropped at 999.md's edge = **temporary IP ban** | `ping 999.md` replies (ICMP allowed) **but** `Test-NetConnection 999.md -Port 443` → `False`, while google:443 → `True`. Browser also blocked. |
| Responses take ~13s each, listings process 1 every ~45s | **999.md soft-throttle** — server intentionally slows (doesn't drop) responses above ~16 combined site connections | A *single* fetch + a 12-concurrent burst from a fresh client both return in <0.5s (so it's not a hard block) — yet the running scraper crawls. The diff is cumulative/combined concurrency. |
| `GET ... failed after 3 attempts: [Errno 11001] getaddrinfo failed` | **DNS resolution failing** — Windows resolver swamped by a reconnect storm + asyncio default-executor starvation | `socket.getaddrinfo('999.md',443)` resolves in 0.01s when run alone; only fails under the scraper's concurrent load. |

**Key discriminator:** browser opens 999.md fine but the scraper is "blocked" ⇒ NOT a dumb IP firewall (that blocks the browser too) ⇒ it's rate/behaviour based ⇒ the lever is volume, not code.

---

## Root cause: the two-process split doubled site concurrency

The `2026-05-28/29` "Change Scrapper Logic" commit split one scraper into **two processes that run simultaneously**:
- `scheduler_f.py` tick — site sem **12** (fast mode)
- `refresher_loop.py` — was site sem **12**, re-fetching all ~89k detail pages back-to-back with a 30s pause

`12 + 12 = 24` concurrent on 999.md. Per `pipeline.py`'s own calibration comment: *"at sem>16 the source server intentionally slows responses (p50 1s → 13s at sem=24)."* So the split **guaranteed** soft-throttle, and sustained volume escalated it into temporary IP bans. The old single-process scheduler "worked fine yesterday" because it was the **only** thing hitting the site (sem 12, under the threshold) and the DB was synced (light ticks).

**Rule:** GraphQL discovery (POST `/graphql`, sequential, 1 reused connection) is tolerated even for the full 1,144-page sweep — it always completes in the logs. The thing that trips the limiter is the **detail-page GET volume**: verify-sold + new-listing detail + photos, multiplied across two processes.

---

## The `getaddrinfo failed` mechanism (Windows + asyncio)

Two compounding causes, both fixed 2026-05-29:

1. **Reconnect storm.** When 999.md throttles and drops connections under a backlog, httpx reopens connections en masse → a burst of DNS lookups → Windows DNS client returns spurious `WSAHOST_NOT_FOUND` (Errno 11001). Mitigation: lower CDN concurrency `32 → 16` so fewer sockets churn.
2. **Default-executor starvation.** `asyncio.getaddrinfo()` runs on the loop's **default** `ThreadPoolExecutor`. Fast mode did `loop.set_default_executor(ThreadPoolExecutor(max_workers=24, name="parse"))` and parsing uses `asyncio.to_thread` → DNS lookups and CPU-bound BeautifulSoup parses **share the same 24 threads**. A backlog of concurrent parses starves DNS of threads. Fix: bump to **48** workers (renamed `io`), leaving headroom for both.

If `getaddrinfo` ever persists after these: pin/cache the host→IP in `scraper/session.py` (resolve once, reuse) — kills it outright.

---

## The backlog loop (why ticks TIMEOUT at 480s)

Independent of bans: when new-listing inserts keep getting interrupted, the feed accumulates listings not in the DB (observed `new=873`, normal is ~30/tick). A single 10-min tick then can't do full discovery (~240s) **plus** 873 new (detail+photos) **plus** verify-sold inside the 480s timeout → TIMEOUT → backlog never drains → next tick identical. A self-perpetuating loop.

**Drain procedure (one-time):**
```
# 1. stop scheduler_f.py AND refresher_loop.py (Ctrl+C)
# 2. uncapped catch-up WITH a safety backup:
python pipeline.py --mode full          # finishes in a few min, inserts the backlog
# 3. restart the scheduler alone:
python scheduler_f.py
# 4. only after ticks are confirmed light, optionally add:
python refresher_loop.py                # now sem 3
```
Why `--mode full` and not loop it forever: `full` hot-backups the DB **before every run**; looping it every 10 min burns the 14 backup slots in ~2h. The scheduler's `tick` mode skips the backup on purpose — that's the whole reason the modes differ.

---

## Final tuning (2026-05-29)

| Knob | Before | After | Why |
|------|--------|-------|-----|
| `scheduler_f` tick | full discovery + verify-sold every 10 min | **(unchanged — restored)** | user requires sold/removed detection every 10 min; needs the *full* crawl to compute `missing_ids` |
| fast-mode `CDN_CONCURRENT_REQUESTS` | 32 | **16** | cut reconnect/DNS storm — **kept** |
| fast-mode default executor | 24 (`parse`) | **48** (`io`) | stop DNS starving behind parses — **kept** |
| `pipeline._touch_all` | 89k UPDATEs in ONE txn | **commit every 1,000** | the `database is locked` fix — **kept** |
| `refresher_loop` SITE_CONCURRENCY | 12 (fast) | tried **3** → **REVERTED to 12** | see below |
| `refresher_loop` targets | all ~89k back-to-back | tried **`refresh_older_than_hours=24`** → **REVERTED to all-known** | see below |
| `refresher_loop` pause / fast | 30s / fast=True | tried **5 min / fast=False** → **REVERTED to 30s / fast=True** | see below |

> **⚠️ The refresher tuning was REVERTED at the user's request (2026-05-29, end of session).** With `refresh_older_than_hours=24` on a freshly-synced DB, the refresher correctly refreshed **0** listings (all were <24h fresh) and each pass finished in ~1s. The user read that idle behaviour as broken — they want the refresher *continuously* re-fetching every listing for price/mileage drift, not waiting 24h between touches. So `refresher_loop.py` is back to its committed state: `fast=True`, **sem 12**, all ~89k known-active per pass, 30s pause; and `pipeline.py`'s `skip_discovery` branch restored its `_touch_all`.
>
> **Consequence (live risk):** this is exactly the config that puts combined site concurrency at scheduler(12)+refresher(12)=**24**, over the ~16 soft-throttle line. If the throttle/`getaddrinfo`/ban symptoms return, the refresher is the lever — the gentle middle ground (continuous full refresh but polite) is `fast=False` (drops to sem 8 + 200–600ms delay) without re-introducing the 24h idle window the user disliked.

**`refresh_older_than_hours=24` semantics (kept for reference):** it refreshes listings whose **`last_fetched_at`** is >24h old (how stale *our* copy is), NOT listings <24h old by post date. First pass is large (everything qualifies); then it self-levels to ~1/24th per hour. This is *correct* behaviour but conflicts with the user's "always be refreshing" expectation.

---

## A misstep to not repeat (mine)

I first "fixed" the bans by making the tick do **shallow discovery** (early-stop after 3 consecutive fully-known pages, ~6 pages instead of 1,144). It cut volume beautifully (validated: 6 pages / 3.3s) — **but a shallow crawl can't see the full catalogue, so it can't compute `missing_ids`, so sold/removed detection silently stopped.** The user needs sold checked every 10 min. Reverted. The shallow params remain in `crawler.py`/`pipeline.py` as inert opt-in (`shallow=False` default). **Lesson: confirm the job's correctness requirements (here: 10-min sold detection) before trading completeness for cheapness.**

---

## Tick survives throttle now — but volume is still the real lever (2026-05-30)

The recurring symptom — a burst tick logs a handful of `(0 photos)` listings, then "freezes" for minutes, then "tick done" — is the throttle/ban/getaddrinfo cascade above. Three changes make the tick *survive* it gracefully instead of hanging (they do **not** reduce the volume that triggers it):

- **`_discover_parallel` (pool=6)** in `crawler.py` — full/tick discovery is now concurrent (~4 min → ~1 min), freeing tick budget. Shallow early-stop stays sequential.
- **Per-listing `asyncio.wait_for` behind a launch gate** (`config.PER_LISTING_TIMEOUT_S = 120`) in `pipeline.py` — kills the actual *freeze*: a DNS lookup starved on the shared executor used to hang a worker forever (httpx's own timeout never starts because the await is stuck waiting for a thread). **The clock starts only after the worker passes a `launch_gate` semaphore (sized `2 × CONCURRENT_REQUESTS`)** — NOT at `gather` time. First attempt got this wrong: every coroutine `gather` launches starts its 120s clock immediately, so listings queued behind the site semaphore timed out *en masse while still waiting for a slot* (308 of them in one instant), falsely tripping the breaker — see [[mistakes#2026-05-30]]. The gate makes the timeout measure fetch time, not queue time.
- **Circuit breaker** (`config.ABORT_AFTER_CONSEC_FAILURES = 40`) — `40` failures back-to-back = throttle/ban; the run aborts early so we stop hammering (which escalates the ban) and let the next tick retry in ~10 min. Any success (incl. photo-less `Cumpăr` buyer posts) resets the streak. **Only meaningful once the gate is correct** — otherwise queue-starvation timeouts trip it spuriously.
- **Tick timeout 8 → 15 min** (`scheduler_f.py`) — start-of-day backlog can drain in one tick; `job_lock` skips overlapping fires.

**Still true:** scheduler(12) + refresher(12) = 24 combined > ~16 throttle line. The breaker means a throttled tick now *ends cleanly in seconds* instead of freezing, but if `(0 photos)`/throttle is chronic, the durable fix is still lowering volume (refresher `fast=False`, or the one-time `--mode full` drain), or merging the two processes behind one global semaphore.

---

[[index|← Vault Index]]
