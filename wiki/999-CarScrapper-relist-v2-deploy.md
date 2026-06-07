# 999 CarScrapper — Relist v2: Shipped Model + Deploy (2026-06-05)

> The session that took the [[999-CarScrapper-relist-identity-rethink|rethink]]
> design from "validated dry-run" to a **shipped, self-healing** clustering
> system: the new tier-A/S/B + clique model, three precision bugs that only
> live-testing surfaced, a batch deploy into `car_identity`, a continuous
> re-cluster daemon, and a search-by-id lookup. Companion to
> [[999-CarScrapper-relist-identity-rethink]] (the *why*) and
> [[999-CarScrapper-relist-phash-tuning]] (the old pHash tuning this supersedes).

Related: [[projects/999-CarScrapper]] · [[todo/999-CarScrapper-todo]] · [[999-CarScrapper-relist-identity-rethink]] · [[999-CarScrapper-dedup-consistency]]

---

## TL;DR

- New model **built + validated full-DB**: year-span≥3 chimeras **540 → 0**, largest cluster **96 → ~26**, spec-conflict rate **16.5% → 11.6%** (and the residue is mostly data noise — typo'd hp/engine on otherwise-identical relists — not real chimeras).
- Deploy is **batch, on a schedule**, deliberately NOT a hot-path rewrite — rarity is a *global* property (a showroom photo only looks common once you've seen all its copies; a per-listing matcher at ingest can't know that, so it would re-introduce chimeras).
- Live `db/database.py` `find_cluster_for_photos` is **UNCHANGED** (still the old 6/3/2 pHash logic). It only assigns *provisional* clusters at ingest; `recluster_loop` overwrites them with the validated model every 30 min.

## The model (`scripts/relist_v2.py`, rewritten)

- **GATE** (necessary): same make + model, |year diff| ≤ 1, same fuel group (petrol/diesel/electric; hybrids→petrol).
- **AD-strip**: a shared photo spanning ≥2 (make,model), ≥2 fuel groups, year-span ≥3, or global freq ≥30 is a reused graphic, not identity.
- A gated pair is the same car iff ANY of:
  - **A — rare photo**: shares a photo with global listing-freq ≤ 2 (unique enough to *be* the car; handles cross-posts + odometer-typo relists).
  - **S — single-car photo**: shares a photo whose carriers resolve to ≤1 distinct `(year,km,eur)` fingerprint **and** no placeholder-mileage carrier (relist-proof: a car relisted 20× still resolves to one fingerprint).
  - **B — fingerprint**: both have an identical non-placeholder `(year,km,eur)` fingerprint, global freq ≤ 8.
  - **S and B additionally require photo OVERLAP**: ≥5 shared photos OR ≥60% of the smaller gallery.
- **CLUSTER = CLIQUE** (Bron–Kerbosch per connected component), never transitive union-find (that's what built the 85-member Peugeot chimera).
- Every evaluated pair → one row in **`relist_decision_log`** (decision, tier, shared rare/single/common counts, min freq, fingerprint dispersion, mileage/price, clique id, human-readable reason). Debug with one SQL query.

## Three precision bugs that live-testing caught (and fixed)

1. **Self-defeating rarity** — a car a dealer relisted 5× inflated its *own* photo + fingerprint frequency past the rarity caps → it got rejected (Dacia Duster, 5 consecutive ids, identical everything). Fix: measure rarity in **identity space** (distinct fingerprints among a photo's carriers), not listing-count → that's tier-S.
2. **Placeholder poisoning** — a photo shared by *one* real car + N new cars with `km=1` had dispersion=1 (placeholders carry no fingerprint) → looked "single-car" → fused a used 2021 PHEV Tucson with new 2022 HEVs. Fix: a `km < 100` carrier disqualifies the single-car path.
3. **Generic-fingerprint chimera** — two different 2001 C-Classes, both at round `300000km / €2550`, sharing a couple of reused photos, fused via tier-B. The pairwise exact-overlap matrix proved two cars (within-car 7–10 shared, cross-car only 2–4). Fix: S/B require strong photo overlap; the bad cross-links fell below it.

(All three were found by the user's instinct — *"check if it has the exact same photos"* — via `lookup.py` + montages, not by the aggregate metrics.)

## Deploy architecture — why batch-on-schedule

- **COMPUTE** = `relist_v2.py` — full DB scan, GLOBAL rarity → writes `relist_decision_log`. ~80s idle, 11–16 min under live scraper contention.
- **DEPLOY** = `scripts/apply_clusters.py` — reads the latest run's cliques and **rebuilds `car_identity`** in one atomic transaction. Only multi-member cliques get a row; singletons stay `car_identity_id = NULL` (per `web/queries.py`: *"NULL-clustered listings are never deduped"* → shown individually). Dry-run reports the diff; `--apply` commits (backup first). **Validated on a hot-copy of the live DB: 0 chimeras, C-Class correctly split.**
- **CONTINUOUS** = `recluster_loop.py` — third daemon; runs compute + deploy every 30 min (`--every-hours` to tune). Each pass wipes+rebuilds with *current* global rarity, so it self-heals (including the provisional clusters ingest created).
- **Ingest left as-is** on purpose. An incremental matcher can't compute global rarity — when the 2nd copy of a future-common showroom photo arrives it momentarily looks rare (freq=2) → would merge two different cars. The 30-min batch is what guarantees correctness. (Considered and rejected an incremental fast-path: it can't meet "won't mismatch relists.")

## Runbook

Fix the DB once (daemons stopped, from the `999 CarScrapper` folder):
```
python -m scripts.relist_v2 --reset-log      # ~80s with daemons down
python -m scripts.apply_clusters --apply     # backup + rebuild car_identity
# then restart: python scheduler_f.py ; python refresher_loop.py
```
Keep it fixed (continuous): `python recluster_loop.py`  (3rd daemon, every 30 min).

Verify / inspect:
- `python -m scripts.apply_clusters` (dry-run) → ~0 changes right after a deploy.
- `python -m scripts.lookup <id> --who` → details + live & new-model cluster + per-pair reasons + montage; **works for deleted listings** (local DB, unlike 999.md).
- Web: paste a listing id in the search box + Enter (works for removed listings).

## Files

- **new** `scripts/apply_clusters.py`, `recluster_loop.py`, `scripts/lookup.py`
- **rewritten** `scripts/relist_v2.py` (full model + decision log)
- **changed** `db/schema.sql` (+`relist_decision_log` table), `web/static/app.js` + `index.html` (search-by-id incl. deleted)
- **unchanged** `db/database.py` ingest matcher (provisional only; the loop is authoritative)

## Verifying the loop is alive (2026-06-05) — the `0 clusters` red herring

User saw `recluster_loop` print `montage pages (0 clusters): 0` on *every* pass and asked "you sure it's working?". **It was working** — the log line is cosmetic noise:

- The loop runs `relist_v2 --montage 0`, so the **montage summary** (`relist_v2.py:749`, the last `print` in the file) is *correctly* zero. The real counts are at `relist_v2.py:658` (`CLIQUE clusters: N`) and `:687` (`logged N decisions`).
- The old loop only echoed **the last 3 stdout lines** (`splitlines()[-3:]`) → it always showed the montage line and hid the real counts.
- `apply_clusters` reports its rebuild via **loguru → stderr**, which the loop printed **only on failure** → `rebuilt N clusters` was never visible on a successful pass.

**Proof it was live** (queried `E:\DB\listings.db` directly): `relist_decision_log` latest run `20260605T224751` (= that pass's `22:47:51`) had **52,338 decisions**; `car_identity` held **16,480** multi-member clusters covering **34,699** listings, ids contiguous `1…16480` (= full wipe+rebuild ran that pass). To check liveness fast: match the newest `relist_decision_log.run_id` timestamp to a recent pass, and confirm `car_identity` id range is contiguous from 1.

**Fix** (`recluster_loop.py`, logging-only — no behavior change): `_run` now returns the `CompletedProcess`; `one_pass` greps `relist_v2` **stdout** for `CLIQUE clusters:` + `logged ` and `apply_clusters` **stderr** for `rebuilt ` → each pass now logs `compute: CLIQUE clusters: …` + `pass deployed: rebuilt N clusters …`. Restart the daemon to pick it up; the running instance keeps clustering correctly, just logs the old line until restarted.

**Lesson**: when a daemon "looks dead" from its log, the log line may just be the wrong signal — verify against the DB/state before touching code (same instinct as the [[999-CarScrapper-dedup-consistency|"508 vs 67"]] non-bug). loguru defaults to stderr, so subprocess wrappers that only print stdout will silently swallow it.

## Tier H — high-overlap merge (SHIPPED 2026-06-06)

**Trigger**: user saw 12 identical `Nissan Primera 2002` listings (one dealer relisting one car: 290 km, €2250, same silver Primera, 9/10 shared photos) showing as separate cards — only 2 were clustered, 10 were singletons. The decision log showed **all three tiers defeated by self-defeating rarity at scale** (this is deploy bug #1, but a 12× relist instead of 5×):

| Tier | Cap | These listings | Why it failed |
|------|-----|----------------|---------------|
| A rare photo | freq ≤ 2 (`--rare-cap`) | rarest shared photo freq **11–13** | dealer reused photos across 12 listings |
| S single-car | dispersion ≤ 1 (`--photo-car-cap`) | dispersion **2** | photos also appear under a 2nd fingerprint globally |
| B fingerprint | freq ≤ 8 (`--meta-rarity-cap`) | fp `(2002,290,2250)` freq **12** | the relist run inflated its own fingerprint past the cap |

The **90% gallery overlap** that obviously identifies them was only a *gate* on S/B (`overlap_ok`), never a merge signal on its own.

**Fix** (`scripts/relist_v2.py`): added **tier H** — `is_H = args.high_overlap and overlap_ok`, i.e. merge when shared photos ≥ `--overlap-min` (5) OR ≥ `--overlap-frac` (60%) of the smaller gallery, **regardless of rarity/fingerprint**. Flag `--high-overlap`, **default OFF** (ad-hoc runs stay precision-first); `recluster_loop.py` passes it explicitly. Also added a `CHIMERA METRICS` stdout line (year-span≥3 / multi-fuel clusters / largest cluster) as the validation signal for any model change.

**Validation (full-DB, `--no-log` baseline vs `--high-overlap`)**:

| | baseline | tier H |
|---|---|---|
| listings clustered | 34,692 | **36,882** (+2,190) |
| clusters | 16,473 | 16,263 (split relists rejoined) |
| year-span≥3 chimeras | 0 | **0** |
| multi-fuel chimeras | 0 | **0** |
| largest cluster | 26 | **26** (no runaway fusion) |

**Why it's safe**: the C-Class chimera (deploy bug #3) had cross-car overlap of only **2–4** photos — below the ≥5 threshold by construction, so tier H *cannot* recreate it; the AD-strip gate still strips reused dealer graphics underneath. Caveat: the chimera metrics are coarse (won't catch same-year/same-fuel look-alikes) — the real guarantee is the threshold + ad-strip, not the metric.

**Deployed**: run `20260606T010429`, `apply_clusters --apply` rebuilt 16,263 clusters / 36,882 listings (1,287 brand-new clusters, 5,856 listings re-grouped). The 12 Primeras → cluster **973** (11 listings) + **972** (the 2 that share only 2 photos with the rest — clique model correctly won't transitively chain them).

**GOTCHA — restart the daemon after a model change**: `recluster_loop.py` runs `relist_v2`/`apply_clusters` as subprocesses, but the *running* daemon holds the old `recluster_loop.py` in memory. After editing its invocation (e.g. adding `--high-overlap`) you MUST Ctrl-C + restart it, or its next pass recomputes with the old flags and **overwrites `car_identity`, silently reverting the deploy**. (Editing `relist_v2.py`/`apply_clusters.py` alone *is* picked up live, since they're re-spawned each pass — only changes to `recluster_loop.py` itself need a restart.)

## Open / not shipped

- ~~**High-overlap path**~~ — **SHIPPED 2026-06-06 as tier H** (see section below).
- **New-model cluster in the web detail** — the detail panel still renders the live `car_identity` cluster (now correct post-deploy); surfacing the per-pair *reasons* in the UI is optional.
- **ORB/AKAZE feature-verify** (blurred-plate recall, reject same-angle look-alikes) — still future.

[[../index|← Vault Index]] · [[projects/999-CarScrapper|← Project]]
