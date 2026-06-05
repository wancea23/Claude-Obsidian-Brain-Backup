# 999 CarScrapper — Relist pHash Tuning (missed dealer relists)

> Why genuine "delete + repost" relists slipped past the cluster matcher and got
> filed as brand-new singleton cars, and the threshold/window tuning + the
> non-destructive re-cluster tool that fixed ~2,748 of them. Companion to
> [[999-CarScrapper-dedup-consistency]] (which covers *counting* clusters; this
> covers *forming* them).

Related: [[999-CarScrapper-dedup-consistency]] · [[projects/999-CarScrapper]] · [[decisions/999-CarScrapper-decisions]] · [[todo/999-CarScrapper-todo]]

---

## Symptom

User spotted two listings of the *same* dark Hyundai Tucson 2022 (interauto.md
dealer) shown as two separate cars in the grid:
- `104436274` — seen 2026-05-23, removed 05-28, 21,999 €, 129,000 km
- `104480077` — seen 2026-05-28, removed 06-02, 21,999 €, 134,000 km

Same photos, same price — obviously one car the dealer deleted and reposted under
a new ID. The `car_identity` pHash de-duplicator exists precisely to catch this,
but it filed them as two singleton clusters (82494 vs 91250).

## Root cause (two compounding factors)

1. **Threshold too strict for CDN re-encodes.** On repost, 999.md's CDN
   re-encodes the *identical* source photo to a fresh `.webp`. That alone drifts
   `imagehash.phash` by ~10 bits. The matcher required Hamming **≤ 6**. Measured
   on the real pair: the same front-3/4 shot scored **10**; matching photos
   ranged **0–14**, several exact 0s.
2. **Scan window too narrow + dealer reordering.** The matcher only examined the
   new listing's **first 3** photos (`PHASH_MATCH_FIRST_N = 3`). Dealers reorder
   the gallery on repost and park a shared promo banner in an early slot (slot 2
   here), which is correctly excluded as a "template" phash (spans ≥2 distinct
   make+model). That left just **2 real photos** in the window — both happened to
   be re-encode-drifted past 6 → **0 matches → new singleton**. The strong
   matches (Hamming 0) sat at photo idx 6/12/18/19, outside the first-3 window.

## Fix (`db/database.py` constants)

| Constant | Old | New | Why |
|---|---|---|---|
| `PHASH_HAMMING_THRESHOLD` | 6 | **10** | Covers CDN re-encode drift (same image lands 0–10). |
| `PHASH_MATCH_FIRST_N` | 3 | **8** | Enough real car photos to survive promo-banner exclusion + gallery reorder. |
| `PHASH_REQUIRED_MATCHES` | 2 | 2 (kept) | Two independent photo matches is still the join bar. |

These constants drive **both** the live pipeline (`pipeline.py` new-listing branch)
and the backfill (`scripts/backfill_phash.py --phase cluster` reads
`db.PHASH_MATCH_FIRST_N` as its photo `LIMIT`).

## Validation method (the part worth reusing)

Don't bump a similarity threshold blind — quantify the false-positive cost first.
Took **40 random distinct Tucsons** in distinct clusters (i.e. presumed different
cars) → **741 pairs** → counted how many would falsely match under each candidate
param set, *with templates excluded and restricted to same make+model*:

| Params | False matches / 741 |
|---|---|
| N=3 thr=6 req=2 (old) | 0 |
| **N=8 thr=10 req=2 (chosen)** | **0** |
| N=8 thr=12 req=2 | 1 ← too loose |
| N=10 thr=10 req=3 | 0 |

thr=10 is the sweet spot: catches the re-encode drift with **zero** FPs; thr=12
starts merging genuinely different same-model cars. The same-(make,model)
candidate restriction + the `assign_cluster` cross-type guard are what make the
looser threshold safe.

## Fixing the historical backlog — `scripts/merge_relists.py` (new tool)

The old fix-the-data path was `reset_clusters` (wipe ALL clusters) + `backfill_phash
--phase cluster` (rebuild). **Rejected here** because: (a) the scheduler +
refresher + web app were all running live → wiping 98k clusters mid-flight races
the scheduler's concurrent re-assignment; (b) it needlessly churns the ~15k
already-correct multi-member clusters.

`merge_relists.py` is the **non-destructive, resumable, lock-tolerant** counterpart:
- Walks listings oldest-first; only revisits ones currently in a **singleton**
  cluster (never touches formed multi-member clusters).
- Runs the **same live logic** (`db.find_cluster_for_photos` with the new params).
- On match, moves the singleton's member(s) into the earlier cluster, sets
  `relisted_from_listing_id`, recomputes aggregates (`listing_count`,
  first/last_seen, `current_listing_id`, status), deletes the emptied singleton.
- ASC-chaining: a later-singleton match is skipped (handled when we reach it);
  multi-member priors are always joined.
- Per-merge transaction + 60 s busy_timeout + 6× retry → coexists with the live
  scheduler. Re-runnable: already-merged listings are no longer singletons, so it
  resumes where it left off.

```
python -m scripts.merge_relists                          # dry-run, all makes
python -m scripts.merge_relists --make Hyundai --model Tucson   # scoped
python -m scripts.merge_relists --apply                  # commit
```

## Results (2026-06-02 run)

- **Hyundai Tucson scoped:** 61 merges / 873 singletons examined (~7% were missed
  relists). Target pair unified into cluster 82494 (count 2, span 05-23→06-02,
  status removed, orphan singleton deleted).
- **Global (all makes):** **2,748** relists merged. Verified against the pre-run
  backup: **0 new chimeras** (the same-make+model gate held), count-mismatches
  *down* 17,209→16,709, multi-member clusters 14,978→16,655.

## Gotchas / follow-ups

- **Long-running daemons cache the old constants.** `scheduler_f.py` and
  `refresher_loop.py` import `db.database` once — they keep matching new relists
  with the OLD threshold until **restarted**. Same lesson as the 2026-05-24
  cluster fix. The historical sweep is independent of this.
- **Refresh path still doesn't self-heal clusters.** Only the `is_new=True` branch
  in `pipeline.py` calls `find_cluster_for_photos`. A listing whose
  `car_identity_id` is NULL on a refresh never gets clustered. See the open todo
  "Self-heal cluster gap on refresh path" — `merge_relists.py` is the manual
  stopgap until that lands.
- **Pre-existing latent bookkeeping debt (NOT from this work):** ~5k orphan
  clusters (0 members) and ~16.7k `listing_count` ≠ actual-member-count exist from
  the original assign/reconcile flow (count increments on join, never decrements;
  orphans left when members soft-archive). Present in the backup too. A
  `reconcile_all_clusters` sweep would clean it; deferred.
