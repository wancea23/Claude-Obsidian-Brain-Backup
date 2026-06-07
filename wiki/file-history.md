# File History — old logic backups

_(No persisted edits yet. A 2026-06-04 attempt to replace `_fuzzy_dedup` in
999 AutoPost was reverted before commit — see the dedup planning note in the
999 AutoPost todo.)_

## Log

### [2026-06-04 16:47] 999 CarScrapper\scripts\audit_relists.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
        for r in con.execute(q, ch):
            members_by_cid.setdefault(r["car_identity_id"], []).append(r)
            lids.append(r["id"])
```

### [2026-06-04 17:22] 999 CarScrapper\web\queries.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    "color": "color",
}


def build_listing_query(params: dict[str, Any]) -> tuple[str, str, list[Any], bool]:
```

### [2026-06-04 17:23] 999 CarScrapper\web\static\index.html
**Change**: (fill in — what changed and why)
**Old value**:
```html
      <input id="search" type="search" placeholder="Search title or descriptionâ€¦ (press / to focus)" />
```

### [2026-06-04 17:24] 999 CarScrapper\web\static\app.js
**Change**: (fill in — what changed and why)
**Old value**:
```javascript
function buildQuery() {
  const f = state.filters;
  const p = new URLSearchParams();
  for (const k of ['q','make','model','status','currency','year_min','year_max',
```

### [2026-06-04 21:28] 999 CarScrapper\scripts\relist_v2.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    ap.add_argument("--sample", type=int, default=30000)
    ap.add_argument("--year-tol", type=int, default=1)
    ap.add_argument("--montage", type=int, default=40)
    ap.add_argument("--seed", type=int, default=7)
```

### [2026-06-04 21:38] 999 CarScrapper\scripts\relist_v2.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--max-link-freq", type=int, default=8)
```

### [2026-06-05 08:26] 999 CarScrapper\scripts\relist_v2.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    montage = bc[:args.montage]
    mont_ids = [i for s in montage for i in list(s)[:MAX_MEMBERS]]
    pbl = {}
    for ch in chunks(mont_ids, 400):
        for r in con.execute(f"SELECT listing_id, idx, phash, filename FROM photos WHERE listing_id IN ({','.join('?'*len(ch))})", ch):
            pbl.setdefault(r["listing_id"], []).append(dict(r))
    cds = []
    for ids in montage:
        ms = sorted(members_of(ids), key=lambda m: m["first_seen_at"] or "")
        extra = ""
        if len(ms) > MAX_MEMBERS:
            extra = f" (+{len(ms)-MAX_MEMBERS} more)"
            ms = ms[:MAX_MEMBERS]
        if len(ms) < 2:
            continue
        cds.append({"n": len(ids), "mm": f"{ms[0]['make']} {ms[0]['model']}",
                    "reasons": ["NEW exact-1:1 relist" + extra], "members": ms})
    pages = make_montage(cds, str(OUT / "relist"), pbl)
```

### [2026-06-05 15:09] 999 CarScrapper\scripts\relist_v2.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    # map a cluster set back to its clique_id so we can print the tier evidence
    set_to_cid = {frozenset(v): k for k, v in clusters.items()}
    bc.sort(key=lambda s: (-len(s), min(s)))
```

### [2026-06-05 16:11] 999 CarScrapper\scripts\relist_v2.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    ph_listings = defaultdict(set)
    ph_fps = defaultdict(set)
    n = 0
```

### [2026-06-05 17:07] 999 CarScrapper\scripts\relist_v2.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    ap.add_argument("--min-shared", type=int, default=2,
                    help="tier B: minimum shared identity photos required alongside the fingerprint.")
```

### [2026-06-05 17:34] 999 CarScrapper\web\static\app.js
**Change**: (fill in — what changed and why)
**Old value**:
```javascript
  $('#search').oninput = debounce(e => { state.filters.q = e.target.value; state.page = 1; pushUrl(); fetchListings(); }, 250);
  $('#search').onkeydown = e => { if (e.key === 'Escape') { e.target.value = ''; state.filters.q = ''; fetchListings(); } };
```

### [2026-06-05 17:34] 999 CarScrapper\web\static\index.html
**Change**: (fill in — what changed and why)
**Old value**:
```html
      <input id="search" type="search" placeholder="Search title or descriptionâ€¦ (press / to focus)" />
```

### [2026-06-05 19:53] 999 CarScrapper\web\static\app.js
**Change**: (fill in — what changed and why)
**Old value**:
```javascript
    else if (k in state.filters) state.filters[k] = v;
  }
}
```

### [2026-06-05 20:22] 999 CarScrapper\scripts\apply_clusters.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    ap.add_argument("--apply", action="store_true", help="Rebuild car_identity. Without this: dry-run.")
    ap.add_argument("--run-id", default=None, help="relist_decision_log run to deploy (default: latest).")
    args = ap.parse_args()
```

### [2026-06-05 20:57] 999 CarScrapper\recluster_loop.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
Run:
    python recluster_loop.py                 # every 6h (default)
    python recluster_loop.py --every-hours 3
"""
```

### [2026-06-05 21:22] 999 CarScrapper\web\queries.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    # LEFT JOIN to a per-listing-min-idx photo row is ~10x cheaper than the
    # original `(SELECT ... LIMIT 1) AS thumb` correlated subquery once
    # the result set is large. Same idea for the price-history aggregate.
    select_cols = """
        listings.id AS id, url, status, make, model, year, generation, body_type, color,
        engine_l, engine_type, power_hp, transmission, drive, mileage_km,
        title, price_eur, price_mdl, price_usd, currency_listed, seller_type, location,
        first_seen_at, last_seen_at, sold_at, removed_at,
        photos.filename AS thumb,
        price_predictions.predicted_eur AS predicted_eur,
        price_predictions.delta_pct AS delta_pct,
        price_predictions.flag AS flag,
        ph_agg.pch_count AS price_change_count,
        ph_agg.pch_min   AS price_min_eur,
        ph_agg.pch_max   AS price_max_eur,
        ph_agg.pch_first AS price_first_eur
    """
    # ph_agg: one row per listing summarising its price_history.
    # pch_first = earliest recorded price; UI derives "latest delta" client-side
    # as `price_eur - price_first_eur` since price_history doesn't include the
    # current row (it's append-on-change-only). Cheap because price_history is
    # indexed on listing_id and most listings have 0-2 history rows.
    join_sql = (
        "LEFT JOIN photos ON photos.listing_id = listings.id AND photos.idx = ("
        "  SELECT MIN(idx) FROM photos p2 WHERE p2.listing_id = listings.id"
        ") "
        "LEFT JOIN price_predictions ON price_predictions.listing_id = listings.id "
        "LEFT JOIN ("
        "  SELECT listing_id,"
        "         COUNT(*) AS pch_count,"
        "         MIN(price_eur) AS pch_min,"
        "         MAX(price_eur) AS pch_max,"
        "         (SELECT price_eur FROM price_history ph2"
        "           WHERE ph2.listing_id = price_history.listing_id"
        "           ORDER BY ph2.recorded_at ASC LIMIT 1) AS pch_first"
        "    FROM price_history"
        "   GROUP BY listing_id"
        ") ph_agg ON ph_agg.listing_id = listings.id"
    )

    count_sql = f"SELECT COUNT(*) FROM listings {where_sql}"
    items_sql = (
        f"SELECT {select_cols} FROM listings {join_sql} {where_sql} {order_sql} "
        f"LIMIT ? OFFSET ?"
    )
    return count_sql, items_sql, args + [page_size, offset], has_user_filters
```

### [2026-06-05 21:24] 999 CarScrapper\scripts\add_web_indexes.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    # listings_over_time chart: GROUP BY date(first_seen_at).
    # SQLite supports expression indexes (3.9+).
    ("idx_listings_date_first_seen",
     "CREATE INDEX IF NOT EXISTS idx_listings_date_first_seen "
     "ON listings(date(first_seen_at))"),
]
```

### [2026-06-05 21:29] 999 CarScrapper\web\static\app.js
**Change**: (fill in — what changed and why)
**Old value**:
```javascript
  await loadMarks();
  await loadFacets();
  if (state.filters.make) {
    $('#f_make').value = state.filters.make;
    await loadModels(state.filters.make);
    if (state.filters.model) $('#f_model').value = state.filters.model;
  }
  await renderKpis();
  await fetchListings();
})();
```

### [2026-06-05 21:33] 999 CarScrapper\scripts\add_web_indexes.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    # Sort-by-price path: ALLOWED_SORTS['price'] orders on the
    # COALESCE(price_eur, price_usd, price_mdl/19.0) expression. An expression
    # index lets SQLite walk in price order and stop at LIMIT instead of
    # full-scanning + sorting every active row (~660 ms -> ~10 ms).
    ("idx_listings_status_price_sort",
     "CREATE INDEX IF NOT EXISTS idx_listings_status_price_sort "
     "ON listings(status, COALESCE(price_eur, price_usd, price_mdl/19.0))"),
]
```

### [2026-06-05 23:04] 999 CarScrapper\recluster_loop.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
def _run(step: list[str]) -> bool:
    """Run `python -m <step>` from the project root; log its last lines."""
    r = subprocess.run([sys.executable, "-m", *step], cwd=str(PROJECT_ROOT),
                       capture_output=True, text=True, timeout=STEP_TIMEOUT_SEC)
    for line in (r.stdout or "").strip().splitlines()[-3:]:
        logger.info("  " + line)
    if r.returncode != 0:
        logger.error(f"step `{' '.join(step)}` failed (rc={r.returncode}): {(r.stderr or '')[-600:]}")
        return False
    return True


def one_pass() -> None:
    if not _run(["scripts.relist_v2", "--reset-log", "--montage", "0"]):
        return
    if not _run(["scripts.apply_clusters", "--apply", "--no-backup"]):
        return
    logger.info("pass: new clusters deployed to car_identity")
```

### [2026-06-06 01:00] 999 CarScrapper\scripts\relist_v2.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    ap.add_argument("--overlap-frac", type=float, default=0.6,
                    help="...or shared photos >= this fraction of the smaller gallery (covers small galleries).")
```

### [2026-06-06 01:04] 999 CarScrapper\recluster_loop.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    compute = _run(["scripts.relist_v2", "--reset-log", "--montage", "0"])
```

### [2026-06-06 17:06] m99gadgets\generate_products.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    "Wearable":          "wearable",
    "Accesoriu":         "accessory",
}
```

### [2026-06-06 17:07] m99gadgets\static\js\app.js
**Change**: (fill in — what changed and why)
**Old value**:
```javascript
      "wearable":          ["W"],
      "accessory":         ["COV"],
    };
    const TYPE_TO_URL_SLUG = {
      "K": "keyboard", "KHE": "keyboard", "M": "mouse",
      "H": "headphones", "GH": "gaming-headphones",
      "EH": "earphones", "MIC": "microphone", "J": "controller",
      "PWR": "powerbank", "W": "wearable", "COV": "accessory",
    };
```

### [2026-06-06 17:08] m99gadgets\static\index.html
**Change**: (fill in — what changed and why)
**Old value**:
```html
      <button class="fb" data-filter="PWR" onclick="setFilter(this)">đź”‹ Powerbank</button>
      <button class="fb sep" disabled>â”‚</button>
```

### [2026-06-06 17:54] m99gadgets\generate_products.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    result = subprocess.run(
        [sys.executable, optimizer, "--convert", "--quiet"],
        capture_output=True, text=True
    )
```

### [2026-06-06 17:57] 999 CarScrapper\scheduler_f.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
TICK_EVERY_MIN = 10
WAL_CHECKPOINT_EVERY_MIN = 60
JOB_TIMEOUT_SEC = {
    "tick": 8 * 60,                 # 8 min â€” must finish before next tick fires
}
```

### [2026-06-06 18:03] m99gadgets\generate_products.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
        # keep any images explicitly listed in the manual file that actually exist
        existing_manual_images = [img for img in manual.get("images", [])
                                  if os.path.isfile(os.path.join(IMAGES_DIR, img))]
```

### [2026-06-07 16:56] gen_lora.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
HOST = "http://127.0.0.1:8188"
OUTDIR = r"C:\Users\johns\ComfyUI-Shared\output"

ap = argparse.ArgumentParser()
ap.add_argument("prompt")
```
