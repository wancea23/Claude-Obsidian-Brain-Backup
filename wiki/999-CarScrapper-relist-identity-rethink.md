# 999 CarScrapper — Relist Identity Rethink (2026-06-04)

> The session where we proved the live pHash relist-clustering has a **systematic
> false-positive problem**, discovered *why* (pHash matches composition, not
> identity), reclassified the SM6 "false positive" as a **real** relist, and
> derived a new identity model around one law: **a value only proves identity if
> it is RARE across the dataset.** Companion to [[999-CarScrapper-relist-phash-tuning]]
> (which only tuned thresholds) and [[999-CarScrapper-dedup-consistency]] (counting).
> Status: **SHIPPED 2026-06-05 — built, validated full-DB, and deployed via batch re-cluster + a continuous daemon. See [[999-CarScrapper-relist-v2-deploy]] for the shipped model, the 3 precision fixes found in testing, and the runbook.**

Related: [[projects/999-CarScrapper]] · [[decisions/999-CarScrapper-decisions]] · [[todo/999-CarScrapper-todo]] · [[999-CarScrapper-relist-phash-tuning]]

---

## TL;DR

1. The live matcher (`db/database.py`: Hamming ≤10, ≥2 of first-8 photos, make+model gate, template = phash spanning ≥2 make+model) produces **~9–12 % wrong merges** among the 16,513 multi-member clusters. Confirmed visually + with a physically-impossible-conflict audit (9.3 % of a 1,000 sample had year-span ≥3 or a mileage *drop* — things one car can't do).
2. **Root cause: pHash measures composition, not identity.** Dealer banners, and especially **same-showroom uniform photos**, make *different cars* hash identically. Proven: two different-mileage Peugeot 3008s share **3 byte-identical 64-bit pHashes**; each phash is shared by **8 different cars** (AUTOPLAZA.MD fleet); the photos are visually indistinguishable even to a vision model.
3. **SM6 was NOT a false positive** — the user reclassified it: same car cross-posted in two cities to reach more buyers. ⇒ **location / seller-type / price / small mileage differences are NOT vetoes.** (This *reverses* the attribute-veto design I had built earlier in the session.)
4. **The unifying law** (from banners → boilerplate → placeholder mileage → showroom photos): every signal — photo hash, description, mileage, price — must pass a *"how rare is this value across the whole dataset?"* gate before it is allowed to vote on identity. A photo shared by 8 cars carries no more identity than `mileage = 1 km` (a placeholder on 2,873 listings; `2025 + 1 km` spans 1,163 different cars).
5. The new model: **gate + two-tier evidence (rare-photo OR common-photo+rare-metadata) + per-pair / clique (no transitive chaining) + ORB feature-verify** for blurred-plate recall.

---

## How we got here (session arc)

- **Audit of the live clusters** (read-only). Sampled 1,000 multi-member clusters, montaged suspects, eyeballed. Found dealer-fleet chimeras everywhere: Mercedes E-Class spanning years 2011/13/16 + hp 170/194/204, Hyundai Tucson mixing two body generations, Ford Focus tied together by an "X auto" banner, Toyota Auris by a "BROAUTO.MD" banner that fills the frame.
- **Data-driven floor:** 93/1,000 clusters had a *physically-impossible* conflict (year-span ≥3 or mileage drop >30k). Extrapolates to ~1,500 definitely-wrong clusters. Produced a list of the 100 highest-confidence wrong merges for the user to verify on 999.md — they confirmed.
- **Built a "search by ID" feature** in the web UI so the user could paste an ad id and see the whole cluster (later reverted by the user — `queries.py`/`index.html` are back to original; the feature is documented in decisions but not in the tree).
- **First attribute-veto design** (city/seller/mileage-drop vetoes). The user then **reclassified SM6 as a real relist**, killing the soft-attribute vetoes.
- **Discovered the photo-collision ceiling** while dry-running the new algo (`scripts/relist_v2.py`) on a 30k batch — see proof below.

---

## The decisive proof — pHash-exact ≠ same car

`relist_v2.py` (exact 1:1 photo + ad-strip + make/model/year/fuel gate) still produced an **85-member Peugeot 3008 "cluster"** = ~15 different cars (each genuinely relisted once: pairs with identical mileage+price like `102330294`/`102330298`) **chained together** by union-find through shared photos.

Found a chimera-forming edge: `102330294` (149,300 km) ↔ `103062011` (158,400 km) — **different cars** — linked by **3 exact (Hamming-0) phashes**, each appearing in **8 listings** (`freq=8`, right at the rarity cap, so *not* caught as a template). Loaded the two colliding photos: identical black 3008, same AUTOPLAZA.MD showroom, same angle — **visually the same photo, two different physical cars.**

> **64-bit pHash collides for different cars shot identically in the same dealer showroom.** The background dominates the low-frequency DCT, so the car barely moves the hash. No Hamming threshold separates "same car" from "different car, same showroom spot"; ad-strip and ≥2-shared don't fix it (the collisions are ≥2 per pair and same-spec).

**Corollary (the hard one):** for fleet dealers with uniform photos, *even the real relist pair's photos are common* (freq 8). So **no photo signal at any threshold can separate same-car from different-car for these fleets — only metadata can** (the real pairs share an exact mileage AND price; the chimera links don't).

---

## The new identity model (proposed, not yet built)

**Guiding rule (user's):** when vague → classify **unique**, never relist. Precision over recall.

**Gate (necessary):** same make + model + |year diff| ≤ 1 + same **fuel group** (petrol / diesel / electric — group hybrids with petrol so a Benzină↔Hibrid relabel doesn't split a real relist).

A **pair** is the same car iff it passes the gate AND **either**:
- **(A) rare-photo path** — shares a photo whose global frequency is ≤ ~2–3 (unique enough to *be* the car). Handles SM6 / cross-posts; tolerates different city/seller/price/mileage.
- **(B) common-photo path** — shares photos AND a *rare* exact **mileage and price** fingerprint (placeholders `0/1/2/NULL`, round numbers, and any value shared by many listings are excluded). Handles fleet relists; rejects the showroom chimera links.

**Structural rules (learned the hard way):**
- **No transitive chaining.** Decide per pair; form a cluster only from *mutually* linked members (clique), never one shared photo bridging A–B–C. Connected-components is what fused the 15 cars.
- **ORB / local-feature verification** is the eventual fix for the **blurred-plate** recall case (a real relist where the seller blurred the plate → photo drifts a few bits and "exact" misses it; description may also differ). ORB matches everything except the blurred patch but rejects a genuinely different car at the same angle. It also catches dealers who literally reuse one file across different cars (where pHash *and* a human can't tell).

### How it scores every known case

| Case | Truth | New model |
|---|---|---|
| SM6 (Cimișlia/private vs Chișinău/dealer, mileage 160k vs 163k) | **real** cross-post | keep — rare photos (freq 2) → tier A |
| Scenic #104529855/#104530333 | real | keep — exact mileage + strong photo overlap |
| Auris #103597125 (seasonal photos differ) | real | keep — exact rare mileage 232,110 (tier B) |
| AUTOPLAZA 3008 fleet | ~15 different cars | split — common photos (freq 8), mileages differ → no tier-B metadata |
| X-auto / BROAUTO / SCHMIE fleets | different cars | split — year/fuel gate + banners are span-≥2 ads |
| Tucson 2 generations | different cars | split — gate (year span, fuel) |

---

## Mileage placeholder finding (sub-agent, 2026-06-04)

`mileage = 1` is a placeholder on **2,873** listings; `0` on 144; NULL on 2,926. `2025 + 1 km` → **1,163 different listings**; round numbers cluster too (`2021 + 149,000` → 144, `2016 + 200,000` → 127). So **mileage can never merge two listings on its own** — only a corroborator (tier B), and only when the exact `year+mileage` value is *rare* (25,076 combos are unique → real fingerprints; the common ones carry zero identity). Same gate as banners and showroom photos: rarity.

---

## Scripts written this session (read-only dry-runs)

- **`scripts/relist_v2.py`** — self-contained NEW-algo dry run. Two passes over all photos: (1) phashes shared by ≥2 listings, (2) per-phash signatures for ad detection. Ad = phash spanning ≥2 (make,model) OR ≥2 fuel groups OR year-span ≥3 OR freq ≥30. Then gate + exact-photo + rarity cap (`--max-link-freq 8`) + `--min-shared 2`, union-find, montages. Output → `E:\DB\audit\relists_v2\` (`relists_batch.txt`, `relist_NN.png`). **This is where the showroom-collision proof came from.** It is NOT the final algorithm — it lacks tier-A/B split, clique clustering, and ORB.
- `scripts/audit_relists.py` + `scripts/list_wrong_relists.py` were written earlier in the session then **removed by the user** (don't assume they exist).

The two passes are slow (~2–14 min depending on DB write-load contention); pass-1 is a `GROUP BY phash HAVING COUNT(DISTINCT listing_id)>=2`.

---

## Open questions / next steps

- [ ] Implement **tier-A + tier-B + clique-only** clustering in `relist_v2.py`; re-run the 30k batch → expect clean *pairs* instead of chimeras.
- [ ] Decide thresholds: rare-photo freq cap (≤2? ≤3?), metadata rarity cutoff, year tolerance (±1?), whether transmission/engine join the gate.
- [ ] **ORB/AKAZE feature verification** prototype on candidate pairs — the only thing that recovers blurred-plate relists *and* rejects showroom look-alikes. Needs opencv + reading the webp files; only runs on gated candidate pairs (cheap).
- [ ] Plate-region OCR / VIN as a trump signal (plates often blurred on 999.md, so partial).
- [ ] Validate on **hard negatives** (same dealer / same lot / same model), never random pairs — the original thr=10 got "0 FP on 741 random Tucsons" yet fails on showroom photos.
- [ ] Only after validation: port into live `db/database.py` `find_cluster_for_photos` / `assign_cluster`, and re-cluster historically (non-destructive, like `merge_relists.py`).

---

## Pitfalls checklist (what keeps killing relist algorithms here)

1. **pHash = composition, not identity.** Different cars in the same showroom hash identically (even Hamming 0).
2. **Banners/boilerplate/placeholder-mileage/showroom-photos are all the same bug:** a common value pretending to be identity. Gate every signal on rarity.
3. **Transitive chaining** turns one bad link into a fleet-sized chimera. Use cliques.
4. **Soft attributes are not vetoes** — a real relist legitimately changes city, seller-type, price, and re-types mileage (SM6).
5. **Validating on random pairs hides the real FPs** — they live in same-dealer/same-lot photos.
6. **Interiors are generic**; weight exterior, and only trust truly-exact interior matches.

[[../index|← Vault Index]] · [[projects/999-CarScrapper|← Project]]
