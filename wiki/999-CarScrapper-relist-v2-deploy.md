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

## Open / not shipped

- **High-overlap path** — a price/mileage-change relist (e.g. `104366816`: same car, €2300 vs €2550, 9/10 identical photos) stays SEPARATE under the strict model (no rare photo, fingerprint differs). A "≥5 shared photos → merge regardless of price/mileage" path would recover these; deferred (precision-first). Lives in `relist_v2`; `recluster_loop` would pick it up automatically.
- **New-model cluster in the web detail** — the detail panel still renders the live `car_identity` cluster (now correct post-deploy); surfacing the per-pair *reasons* in the UI is optional.
- **ORB/AKAZE feature-verify** (blurred-plate recall, reject same-angle look-alikes) — still future.

[[../index|← Vault Index]] · [[projects/999-CarScrapper|← Project]]
