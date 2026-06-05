# 999 CarScrapper — Dedup Consistency (unique cars vs raw listings)

> The single most recurring class of bug on this project: a number computed over
> **raw listing rows** sitting next to a number computed over **unique physical
> cars** (cluster-deduped). They look like they should match, they don't, and the
> user reads it as "one of these is wrong." This page is the canonical reference
> for every dedup variant and the rule for keeping them in sync.

Related: [[999-CarScrapper-ratelimit-throttle-dns]] · [[projects/999-CarScrapper]] · [[decisions/999-CarScrapper-decisions]]

---

## The core concept

A physical car relisted under several IDs is grouped into one **`car_identity`
cluster** (pHash of the first **8** photos, Hamming **≤ 10**, ≥2 must match —
loosened 2026-06-02 from the original first-3/≤6 because CDN re-encodes drift a
reposted photo ~10 bits; see [[999-CarScrapper-relist-phash-tuning]]).
`listings.car_identity_id` points at the cluster; NULL means a standalone listing
(most rows). "Unique cars" = collapse each cluster to ONE row.

The grid the user actually scrolls is **deduped**. So every count shown next to it
must be deduped the same way, or it reads as a bug.

## The dedup variants (must stay mutually consistent)

| Surface | Code | Dedup rule |
|---|---|---|
| **Listing grid** | `web/queries.py:build_listing_query` | Per current status, keep **newest sibling** per cluster (`first_seen_at` desc, tiebreak `id` desc). Removed/all also **hide clusters with an active sibling** (a relist isn't a sale). |
| **model_stats Active headline** | `analytics.py:model_stats` | `COUNT(DISTINCT COALESCE(car_identity_id, -id))` — one per cluster; `-id` keeps standalones distinct. |
| **model_stats Sold counts** | `analytics.py` `_dedup_sql()` | relisting filter **+** cluster-dedup (newest removed sibling). |
| **Sell-through tab** | `analytics.py:sell_through_segments` | matches model_stats exactly (active = NOT EXISTS newest-active; sold = `_dedup_sql`). |
| **Year breakdown — active** | `analytics.py:model_stats._active_year_rows` | newest-active-sibling cluster dedup, `COUNT(*)` per year → sums to the Active headline. |
| **Year breakdown — removed** | `analytics.py:model_stats._removed_year_rows` | `_dedup_sql` → sums to Sold total. |
| **Make / Model dropdown counts** | `app.py:_dedup_where` | **mirrors the grid** per status. |

## The golden rule

> Any count rendered next to the grid — headline, side-card tile, year chip,
> dropdown `(N)` — MUST use the **same per-status cluster-dedup the grid uses**.
> Raw `COUNT(*)` is only acceptable for internal metrics never shown beside a
> deduped number.

When adding a new counted surface: reach for `app.py:_dedup_where(status)` (matches
the grid) or, inside `analytics.py`, `_dedup_sql()` / the newest-active-sibling
NOT EXISTS clause. **Don't hand-roll a third variant** — that's how they drift.

## Gotchas learned the hard way

- **Per-year `COUNT(DISTINCT cluster)` double-counts.** A cluster whose relisted
  siblings carry mismatched model-year typos lands in two year buckets, so the
  chips sum to *more* than the headline (saw 511 vs 508). Fix: keep exactly **one
  representative row per cluster** (newest sibling), then plain `COUNT(*)` per year.
  Now sums exactly.
- **`year IS NULL` cars can't be bucketed.** An unfiltered all-makes active
  breakdown sums to slightly *under* the headline (e.g. 63 687 vs 63 707 = 20 cars
  with no model year). This is correct, not a bug — surface it rather than fudge.
- **Status drives meaning, not just rows.** The year breakdown was hardwired to the
  *sold* set regardless of the Active/Removed/All toggle, so under "Active 508" it
  showed chips summing to 67 (sold). Now `status` flows
  `app.js buildQuery → app.py → model_stats(status=…)` and the chips + heading
  follow the toggle ("Active / Sold / Listings by model year").
- **`status` was being stripped** at the model_stats endpoint (`app.py`) — it's not
  a `build_extra_filters` key, so it has to be forwarded explicitly **and** folded
  into the cache key (or Active/Removed/All collide in cache).
- **`_NOT_BUYER` duplication.** Defined in both `app.py` and `analytics.py`; if one
  drifts, one set of endpoints silently inflates. (Still on the todo to consolidate
  into `queries.py`.)

## History of dedup fixes (chronological)

- **2026-05-22** — pHash clusters introduced; unique-car Active count
  (`COUNT(DISTINCT COALESCE(car_identity_id,-id))`) + duplicates tooltip.
- **2026-05-23** — truly-sold counts (`sold_*_truly`), `_NOT_BUYER` plugged into
  analytics so top-bar KPI matched the side-card.
- **2026-05-27** — extracted `_cluster_dedup_sql` / `_dedup_sql`; fixed sold counts
  to apply relisting **+** cluster dedup; sell-through tab switched to identical
  dedup so cross-page numbers match.
- **2026-05-30** — year breakdown made status-aware + summing exactly to its
  headline; Make/Model dropdown counts deduped via `_dedup_where` (BMW 10231→8642,
  matching the grid). *(this session)*

[[../index|← Vault Index]] · [[projects/999-CarScrapper|← Project]]
