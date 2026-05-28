
## Log

### [2026-05-28 later] 999 CarScrapper\pipeline.py
**Change**: Two follow-on fixes. (1) Re-added `skip_discovery` + `skip_backup` params to `run()` — refresher uses these to avoid racing the scheduler on `INSERT OR REPLACE` (which CASCADE-wipes the other process's photos). (2) Added `conn.commit()` after each worker's writes — releases the SQLite write lock between listings so the scheduler's tick doesn't time out with `database is locked` (chunk used to hold the write lock for ~17 min).
**Old value** (buggy intermediate state — held write lock for the entire chunk):
```python
# Worker had no inline commit; relied on `with db.connect()` exit at chunk end.
if is_new: db.insert_listing(conn, data) ...
else:      db.update_listing(conn, data) ...
progress["done"] += 1   # no conn.commit() here
```

### [2026-05-28] 999 CarScrapper\pipeline.py
**Change**: Worker now takes a shared `conn` arg instead of opening per-listing. Chunk loop now wraps a single Session + one db.connect() per chunk.
**Old value**:
```python
def make_worker(session: Session):
    async def worker(lid: int, is_new: bool):
        ...
        with db.connect() as conn:   # per-listing connect/commit/close
            if is_new: db.insert_listing(conn, data) ...
            else:      db.update_listing(conn, data) ...

for chunk_start in range(0, total_targets, chunk_size):
    chunk = scrape_targets[chunk_start:chunk_start + chunk_size]
    async with Session() as session:   # new session per chunk
        w = make_worker(session)
        await asyncio.gather(*(w(lid, lid in new_ids) for lid in chunk))
```

### [2026-05-28] 999 CarScrapper\config.py
**Change**: SCRAPE_CHUNK_SIZE 500 → 2000 (paired with shared session/conn refactor; fewer chunk boundaries amortizes overhead further).
**Old value**:
```python
SCRAPE_CHUNK_SIZE = 500
```

### [2026-05-28] 999 CarScrapper\scheduler_f.py
**Change**: Locked to tick-only. Removed `incr` and `full` jobs + their schedule lines + INCR_TIMES/INCR_REFRESH_HOURS/FULL_DAY/FULL_TIME constants. Refresh now handled by sibling `refresher_loop.py` process.
**Old value**:
```python
INCR_TIMES = ("10:00", "18:00")
INCR_REFRESH_HOURS = 12
FULL_DAY = "sunday"
FULL_TIME = "04:00"
JOB_TIMEOUT_SEC = {"tick": 8*60, "incr": 45*60, "full": 6*60*60}

def job_incr(): _run_job("incr", lambda: run(mode="full", refresh_known=True, refresh_older_than_hours=INCR_REFRESH_HOURS, fast=True))
def job_full(): _run_job("full", lambda: run(mode="full", refresh_known=True, fast=True))

schedule.every(TICK_EVERY_MIN).minutes.do(job_tick)
for t in INCR_TIMES: schedule.every().day.at(t).do(job_incr)
getattr(schedule.every(), FULL_DAY).at(FULL_TIME).do(job_full)
```

### [2026-05-26 22:24] m99gadgets\generate_products.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    og_title_ro = clean + (f" â€” {price} MDL" if price else "") + " | M99 Gadgets Moldova"
    og_title_ru = clean + (f" â€” {price} MDL" if price else "") + " | M99 Gadgets ĐśĐľĐ»Đ´ĐľĐ˛Đ°"
```

### [2026-05-27 19:10] 999 CarScrapper\web\analytics.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    _RELISTED_GAP = (
        "AND (car_identity_id IS NULL OR NOT EXISTS ("
        " SELECT 1 FROM listings sib "
        " WHERE sib.car_identity_id = listings.car_identity_id "
        "   AND sib.status = 'active'"
        "))"
    )
    sold_total_truly = _scalar(conn,
        f"SELECT COUNT(*) FROM listings "
        f"WHERE {REMOVED_FILTER}{mm_sql}{extra_sql} {_RELISTED_GAP}",
        base_args) or 0
    sold_recent_truly = _scalar(conn, f"""
        SELECT COUNT(*) FROM listings
        WHERE {REMOVED_FILTER}{mm_sql}{extra_sql}
          AND COALESCE(removed_at, sold_at) >= datetime('now', ?)
          {_RELISTED_GAP}
    """, window_args) or 0
    avg_days = _scalar(conn, f"""
        SELECT AVG({DAYS_EXPR}) FROM listings
        WHERE {REMOVED_FILTER}{mm_sql}{extra_sql}
          AND COALESCE(removed_at, sold_at) >= datetime('now', ?)
    """, window_args)
    # Average final price of recently-sold rows. Fetch (first_price, final_price)
    # pairs so we can drop "prank" rows whose final price dropped â‰Ą35% from the
    # original asking price â€” those are almost always typos / placeholder edits,
    # not real sales, and would skew the average downward.
    price_rows = conn.execute(f"""
        WITH bounds AS (
          SELECT listing_id,
                 MIN(recorded_at) AS ra_first,
                 MAX(recorded_at) AS ra_last
          FROM price_history GROUP BY listing_id
        )
        SELECT pf.price_eur AS first_p, pl.price_eur AS final_p
        FROM listings l
        JOIN bounds b ON b.listing_id = l.id
        JOIN price_history pf ON pf.listing_id = l.id AND pf.recorded_at = b.ra_first
        JOIN price_history pl ON pl.listing_id = l.id AND pl.recorded_at = b.ra_last
        WHERE l.status IN ('sold','removed')
          AND COALESCE(l.removed_at, l.sold_at) IS NOT NULL
          AND COALESCE(l.removed_at, l.sold_at) >= datetime('now', ?)
          AND pl.price_eur IS NOT NULL{mm_sql_l}{extra_sql_l}
    """, (f"-{int(recent_days)} days", *mm_args, *extra_args)).fetchall()
```

### [2026-05-27 19:12] 999 CarScrapper\web\static\app.js
**Change**: (fill in — what changed and why)
**Old value**:
```javascript
    const soldRecentInfo = relRecent > 0
      ? `${fmtNum(s.sold_recent)} listings were deleted in the last ${s.recent_days} days â€” ${relRecent} ${relRecent === 1 ? 'was' : 'were'} relisted and are still active, so they don't count as sold.`
      : `${fmtNum(s.sold_recent)} listings deleted in the last ${s.recent_days} days. No relistings.`;
    const soldTotalInfo = relTotal > 0
      ? `${fmtNum(s.sold_total)} listings were deleted overall â€” ${relTotal} ${relTotal === 1 ? 'was' : 'were'} relisted and are still active.`
      : `${fmtNum(s.sold_total)} listings deleted overall. No relistings.`;
```

### [2026-05-27 19:39] 999 CarScrapper\web\analytics.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
from __future__ import annotations

import sqlite3
from typing import Any
```

### [2026-05-27 19:41] 999 CarScrapper\web\app.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
# ---------- ML (web/ml.py) ----------
```

### [2026-05-27 19:41] 999 CarScrapper\web\static\index.html
**Change**: (fill in — what changed and why)
**Old value**:
```html
    <button class="tab" data-tab="favorites">Favorites <span id="favCount" class="pill"></span></button>
```

### [2026-05-27 19:42] 999 CarScrapper\web\static\app.js
**Change**: (fill in — what changed and why)
**Old value**:
```javascript
  $('#browseView').hidden = name !== 'browse';
  $('#dashboardView').hidden = name !== 'dashboard';
  $('#analysisView').hidden = name !== 'analysis';
  $('#favoritesView').hidden = name !== 'favorites';
  $('#filters').style.display = name === 'browse' ? '' : 'none';
  // Collapse the 260px filter column so non-Browse tabs use the full width.
  document.body.dataset.tab = name;
  if (name === 'dashboard') renderDashboard();
  if (name === 'analysis') renderAnalysis();
  if (name === 'favorites') renderFavorites();
```

### [2026-05-27 19:44] 999 CarScrapper\web\static\style.css
**Change**: (fill in — what changed and why)
**Old value**:
```css
.detail-card::-webkit-scrollbar-thumb:hover,
.filters::-webkit-scrollbar-thumb:hover,
.thumbs::-webkit-scrollbar-thumb:hover {
  background-color: var(--border-strong);
}
```

### [2026-05-27 19:45] 999 CarScrapper\web\analytics.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
def _dedup_sql(pfx: str = "") -> str:
    """AND clause: relisting filter + cluster dedup for sold listings."""
    p = f"{pfx}." if pfx else ""
```

### [2026-05-27 19:53] 999 CarScrapper\web\analytics.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
def _year_bucket(year: int) -> str:
    base = (year // 4) * 4
    return f"{base}-{base + 3}"


def _generation_label(generation: str | None, year: int | None) -> str:
    if generation:
        m = _YEAR_RANGE_RE.search(generation)
        if m:
            g_start, g_end = int(m.group(1)), int(m.group(2))
            if g_end - g_start > 4 and year:
                return f"{generation} ({_year_bucket(year)})"
            return generation
        return generation
    if year:
        return _year_bucket(year)
    return "Unknown"
```

### [2026-05-27 19:54] 999 CarScrapper\web\app.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
@app.get("/api/analytics/sell_through_segments")
def analytics_sell_through_segments(request: Request, time_window: int = 90,
                                     min_n: int = 5) -> list:
    params = dict(request.query_params)
    filter_params = {k: v for k, v in params.items()
                     if k not in ("time_window", "min_n")}
    key = "st_segments:" + ":".join(f"{k}={v}" for k, v in sorted(params.items()))
    def _impl():
        with db() as conn:
            return analytics.sell_through_segments(
                conn, filters=filter_params, time_window=time_window, min_n=min_n)
    return cached(key, _impl)


@app.get("/api/analytics/sell_through_heatmap_filtered")
def analytics_sell_through_heatmap_f(request: Request, time_window: int = 90,
                                      dimension: str = "body_type") -> dict:
    params = dict(request.query_params)
    filter_params = {k: v for k, v in params.items()
                     if k not in ("time_window", "dimension")}
    key = "st_heatmap_f:" + ":".join(f"{k}={v}" for k, v in sorted(params.items()))
    def _impl():
        with db() as conn:
            return analytics.sell_through_heatmap_filtered(
                conn, dimension=dimension, filters=filter_params,
                time_window=time_window)
    return cached(key, _impl)
```

### [2026-05-27 19:55] 999 CarScrapper\web\static\app.js
**Change**: (fill in — what changed and why)
**Old value**:
```javascript
/* ---------------- sell-through tab ---------------- */
state.stFilters = {
  time_window: 90, min_n: 5,
  year_min: '', year_max: '',
  fuel: new Set(), transmission: new Set(), body_type: new Set(),
  mileage_min: '', mileage_max: '',
  engine_min: '', engine_max: '',
  heatmap_dimension: 'body_type',
};
let _stSegments = [];
let _stSort = { col: 'sell_through_pct', dir: 'desc' };

function buildStQuery() {
  const f = state.stFilters;
  const p = new URLSearchParams();
  p.set('time_window', f.time_window);
  p.set('min_n', f.min_n);
  for (const k of ['year_min','year_max','mileage_min','mileage_max','engine_min','engine_max']) {
    if (f[k]) p.set(k, f[k]);
  }
  for (const k of ['fuel','transmission','body_type']) {
    if (f[k].size) p.set(k, [...f[k]].join(','));
  }
  p.set('dimension', f.heatmap_dimension);
  return p;
}

async function renderSellthrough() {
  const host = $('#sellthroughContent');
  host.innerHTML = '<div class="empty">Loading sell-through data...</div>';
  const qp = buildStQuery();
  try {
    const facets = state.facets || await api('/api/facets?status=active');
    const [segments, heatmap] = await Promise.all([
      api('/api/analytics/sell_through_segments?' + qp),
      api('/api/analytics/sell_through_heatmap_filtered?' + qp),
    ]);
    _stSegments = segments;
    _stSort = { col: 'sell_through_pct', dir: 'desc' };

    host.innerHTML = `
      ${stFiltersHTML(facets)}
      <div class="st-grid">
        <div class="dash-card" id="stTableCard">
          <h3>Segment Sell-through Ranking</h3>
          <div class="st-tbl-scroll" id="stTableWrap">${stSegmentTable(segments)}</div>
        </div>
        <div class="dash-card" id="stHeatmapCard">
          <h3>Sell-through Heatmap</h3>
          ${stHeatmapHTML(heatmap)}
        </div>
      </div>`;
    wireStFilters();
    wireStSorting();
  } catch (e) {
    host.innerHTML = `<div class="empty">Error loading sell-through data: ${esc(e.message)}</div>`;
  }
}

function stFiltersHTML(facets) {
  const f = state.stFilters;
  const timeBtn = (val) => `<button class="st-time-btn${f.time_window === val ? ' active' : ''}" data-tw="${val}">${val}d</button>`;
  const chipSet = (key, values) => values.map(v =>
    `<button class="st-chip${f[key].has(v) ? ' active' : ''}" data-key="${key}" data-val="${esc(v)}">${esc(v)}</button>`
  ).join('');
  const dimOpt = (val, label) => `<option value="${val}"${f.heatmap_dimension === val ? ' selected' : ''}>${label}</option>`;

  return `<div class="st-filters">
    <div class="st-field">
      <span>Time window</span>
      <div class="st-seg">${timeBtn(30)}${timeBtn(60)}${timeBtn(90)}${timeBtn(180)}</div>
    </div>
    <div class="st-field">
      <span>Min sample</span>
      <input type="number" id="st_min_n" value="${f.min_n}" min="1" max="100" class="st-input small">
    </div>
    <div class="st-field">
      <span>Year</span>
      <div class="st-range"><input type="number" id="st_year_min" placeholder="from" value="${f.year_min}" class="st-input"><input type="number" id="st_year_max" placeholder="to" value="${f.year_max}" class="st-input"></div>
    </div>
    <div class="st-field">
      <span>Mileage (km)</span>
      <div class="st-range"><input type="number" id="st_mileage_min" placeholder="from" value="${f.mileage_min}" class="st-input"><input type="number" id="st_mileage_max" placeholder="to" value="${f.mileage_max}" class="st-input"></div>
    </div>
    <div class="st-field">
      <span>Engine (L)</span>
      <div class="st-range"><input type="number" id="st_engine_min" placeholder="from" value="${f.engine_min}" class="st-input" step="0.1"><input type="number" id="st_engine_max" placeholder="to" value="${f.engine_max}" class="st-input" step="0.1"></div>
    </div>
    <div class="st-field">
      <span>Fuel</span>
      <div class="st-chips">${chipSet('fuel', facets.engine_types || [])}</div>
    </div>
    <div class="st-field">
      <span>Transmission</span>
      <div class="st-chips">${chipSet('transmission', facets.transmissions || [])}</div>
    </div>
    <div class="st-field">
      <span>Body type</span>
      <div class="st-chips">${chipSet('body_type', facets.body_types || [])}</div>
    </div>
    <div class="st-field">
      <span>Heatmap dimension</span>
      <select id="st_dimension" class="st-input">
        ${dimOpt('body_type','Body type')}${dimOpt('engine_type','Fuel type')}${dimOpt('transmission','Transmission')}${dimOpt('drive','Drive')}${dimOpt('location','Location')}
      </select>
    </div>
  </div>`;
}

function stSegmentTable(segments) {
  if (!segments.length) return '<div class="empty">No segments meet the minimum sample size.</div>';
  const arrow = (col) => _stSort.col === col ? (_stSort.dir === 'asc' ? ' â†‘' : ' â†“') : '';
  return `<table class="dash-tbl st-tbl"><thead><tr>
    <th data-col="make">Make${arrow('make')}</th>
    <th data-col="model">Model${arrow('model')}</th>
    <th data-col="generation_label">Generation${arrow('generation_label')}</th>
    <th class="num" data-col="sell_through_pct">Sell-through %${arrow('sell_through_pct')}</th>
    <th class="num" data-col="active_count">Active${arrow('active_count')}</th>
    <th class="num" data-col="sold_count">Sold${arrow('sold_count')}</th>
    <th class="num" data-col="avg_days">Avg Days${arrow('avg_days')}</th>
    <th class="num" data-col="avg_price_eur">Avg Price${arrow('avg_price_eur')}</th>
  </tr></thead><tbody>
    ${segments.map(r => `<tr>
      <td>${esc(r.make)}</td>
      <td>${esc(r.model)}</td>
      <td>${esc(r.generation_label)}</td>
      <td class="num"><strong>${r.sell_through_pct}%</strong></td>
      <td class="num">${fmtNum(r.active_count)}</td>
      <td class="num">${fmtNum(r.sold_count)}</td>
      <td class="num">${r.avg_days ?? 'â€”'}</td>
      <td class="num">${r.avg_price_eur ? fmtNum(r.avg_price_eur) + ' â‚¬' : 'â€”'}</td>
    </tr>`).join('')}
  </tbody></table>`;
}

function stHeatmapHTML(h) {
  if (!h.segments.length || !h.dimension_values.length) return '<div class="empty">Not enough data for heatmap.</div>';
  const accent = themeColor('--accent', '#0d9488');
  return `<div class="heatmap-wrap"><table class="heatmap"><thead><tr>
    <th></th>${h.dimension_values.map(v => `<th title="${esc(v)}">${esc(v.length > 8 ? v.slice(0,7) + 'â€¦' : v)}</th>`).join('')}
  </tr></thead><tbody>
    ${h.segments.map((seg, i) => `<tr>
      <td class="row-label" title="${esc(seg)}">${esc(seg.length > 30 ? seg.slice(0,28) + 'â€¦' : seg)}</td>
      ${h.grid[i].map(c => {
        if (!c.n) return '<td class="cell n0" title="no data">Â·</td>';
        const a = Math.min(1, (c.pct || 0) / 50);
        return `<td class="cell" style="background:color-mix(in srgb, ${accent} ${Math.round(a*100)}%, transparent)"
          title="${esc(seg)} (${c.removed}/${c.n}) â€” ${c.pct}%">${c.pct ?? 'Â·'}</td>`;
      }).join('')}
    </tr>`).join('')}
  </tbody></table></div>`;
}

function wireStFilters() {
  const reload = debounce(() => renderSellthrough(), 400);
  $$('.st-time-btn').forEach(b => b.onclick = () => {
    state.stFilters.time_window = parseInt(b.dataset.tw);
    renderSellthrough();
  });
  $$('.st-chip').forEach(b => b.onclick = () => {
    const s = state.stFilters[b.dataset.key];
    if (s.has(b.dataset.val)) s.delete(b.dataset.val); else s.add(b.dataset.val);
    renderSellthrough();
  });
  const numField = (id, key) => {
    const el = document.getElementById(id);
    if (el) el.oninput = () => { state.stFilters[key] = el.value; reload(); };
  };
  numField('st_min_n', 'min_n');
  numField('st_year_min', 'year_min');
  numField('st_year_max', 'year_max');
  numField('st_mileage_min', 'mileage_min');
  numField('st_mileage_max', 'mileage_max');
  numField('st_engine_min', 'engine_min');
  numField('st_engine_max', 'engine_max');
  const dimSel = document.getElementById('st_dimension');
  if (dimSel) dimSel.onchange = () => { state.stFilters.heatmap_dimension = dimSel.value; renderSellthrough(); };
}

function wireStSorting() {
  $$('.st-tbl th[data-col]').forEach(th => {
    th.style.cursor = 'pointer';
    th.onclick = () => {
      const col = th.dataset.col;
      if (_stSort.col === col) _stSort.dir = _stSort.dir === 'desc' ? 'asc' : 'desc';
      else { _stSort.col = col; _stSort.dir = 'desc'; }
      const dir = _stSort.dir === 'asc' ? 1 : -1;
      _stSegments.sort((a, b) => {
        const va = a[col], vb = b[col];
        if (va == null && vb == null) return 0;
        if (va == null) return 1;
        if (vb == null) return -1;
        if (typeof va === 'string') return dir * va.localeCompare(vb);
        return dir * (va - vb);
      });
      const wrap = document.getElementById('stTableWrap');
      if (wrap) wrap.innerHTML = stSegmentTable(_stSegments);
      wireStSorting();
    };
  });
}
```

### [2026-05-27 19:56] 999 CarScrapper\web\static\style.css
**Change**: (fill in — what changed and why)
**Old value**:
```css
/* ---- Sell-through tab ---- */
.st-filters {
  display: flex; flex-wrap: wrap; gap: 12px; align-items: end;
  padding: 14px 16px; background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); margin-bottom: 16px;
}
.st-field { display: flex; flex-direction: column; gap: 3px; min-width: 100px; }
.st-field > span { font-size: 11px; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: .5px; }
.st-input { background: var(--bg); border: 1px solid var(--border); color: var(--text);
  border-radius: var(--radius); padding: 5px 8px; font-size: 13px; width: 100%; }
.st-input.small { width: 60px; }
.st-range { display: flex; gap: 4px; }
.st-range .st-input { width: 70px; }
.st-seg { display: flex; gap: 0; }
.st-seg button, .st-time-btn {
  background: var(--bg); border: 1px solid var(--border); color: var(--muted);
  padding: 5px 10px; font-size: 12px; cursor: pointer; transition: .15s;
}
.st-seg button:first-child { border-radius: var(--radius) 0 0 var(--radius); }
.st-seg button:last-child { border-radius: 0 var(--radius) var(--radius) 0; }
.st-seg button:not(:first-child) { border-left: 0; }
.st-seg button.active, .st-time-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.st-chips { display: flex; flex-wrap: wrap; gap: 4px; max-width: 400px; }
.st-chip {
  background: var(--bg); border: 1px solid var(--border); color: var(--muted);
  padding: 3px 8px; font-size: 11px; border-radius: 999px; cursor: pointer; transition: .15s;
}
.st-chip.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.st-grid { display: grid; grid-template-columns: 1fr; gap: 16px; }
.st-tbl-scroll { max-height: 600px; overflow-y: auto; }
.st-tbl th[data-col] { cursor: pointer; user-select: none; white-space: nowrap; }
.st-tbl th[data-col]:hover { color: var(--accent); }
@media (max-width: 800px) { .st-filters { flex-direction: column; } }
```

### [2026-05-27 20:01] 999 CarScrapper\web\analytics.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
def _dedup_sql(pfx: str = "") -> str:
    """AND clause: relisting filter + cluster dedup for sold listings."""
    p = f"{pfx}." if pfx else "listings."
    return (
        f"AND ({p}car_identity_id IS NULL OR NOT EXISTS ("
        f" SELECT 1 FROM listings sib"
        f" WHERE sib.car_identity_id = {p}car_identity_id"
        f"   AND sib.status = 'active'"
        f"))"
        f" AND ({p}car_identity_id IS NULL OR NOT EXISTS ("
        f" SELECT 1 FROM listings sib"
        f" WHERE sib.car_identity_id = {p}car_identity_id"
        f"   AND sib.id != {p}id"
        f"   AND sib.status IN ('sold','removed')"
        f"   AND (sib.first_seen_at > {p}first_seen_at"
        f"     OR (sib.first_seen_at = {p}first_seen_at AND sib.id > {p}id))"
        f"))"
    )
```

### [2026-05-27 20:02] 999 CarScrapper\web\app.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
@app.get("/api/analytics/sell_through_segments")
def analytics_sell_through_segments(time_window: int = 90,
                                     min_n: int = 5) -> list:
    key = f"st_segments:{time_window}:{min_n}"
    def _impl():
        with db() as conn:
            return analytics.sell_through_segments(
                conn, time_window=time_window, min_n=min_n)
    return cached(key, _impl)
```

### [2026-05-27 20:03] 999 CarScrapper\web\static\app.js
**Change**: (fill in — what changed and why)
**Old value**:
```javascript
/* ---------------- sell-through tab ---------------- */
let _stSegments = [];
let _stSort = { col: 'sell_through_pct', dir: 'desc' };
let _stTimeWindow = 90;
let _stMinN = 5;

async function renderSellthrough() {
  const host = $('#sellthroughContent');
  host.innerHTML = '<div class="empty">Loading sell-through data...</div>';
  try {
    const segments = await api(`/api/analytics/sell_through_segments?time_window=${_stTimeWindow}&min_n=${_stMinN}`);
    _stSegments = segments;
    _stSort = { col: 'sell_through_pct', dir: 'desc' };

    host.innerHTML = `
      <div class="st-header">
        <h2>Top Sell-through Rates</h2>
        <div class="st-controls">
          <div class="st-field">
            <span>Window</span>
            <div class="st-seg">
              ${[30,60,90,180].map(v => `<button class="st-time-btn${_stTimeWindow === v ? ' active' : ''}" data-tw="${v}">${v}d</button>`).join('')}
            </div>
          </div>
          <div class="st-field">
            <span>Min sample</span>
            <input type="number" id="st_min_n" value="${_stMinN}" min="1" max="50" class="st-input small">
          </div>
          <div class="st-meta">${fmtNum(segments.length)} combos</div>
        </div>
      </div>
      <div class="st-tbl-scroll" id="stTableWrap">${stSegmentTable(segments)}</div>`;
    wireStControls();
    wireStSorting();
  } catch (e) {
    host.innerHTML = `<div class="empty">Error: ${esc(e.message)}</div>`;
  }
}

function stSegmentTable(segments) {
  if (!segments.length) return '<div class="empty">No segments meet the minimum sample size.</div>';
  const arrow = (col) => _stSort.col === col ? (_stSort.dir === 'asc' ? ' â†‘' : ' â†“') : '';
  return `<table class="dash-tbl st-tbl"><thead><tr>
    <th data-col="make">Make${arrow('make')}</th>
    <th data-col="model">Model${arrow('model')}</th>
    <th data-col="generation">Generation${arrow('generation')}</th>
    <th data-col="fuel">Fuel${arrow('fuel')}</th>
    <th data-col="mileage">Mileage${arrow('mileage')}</th>
    <th data-col="body">Body${arrow('body')}</th>
    <th class="num" data-col="sell_through_pct">ST %${arrow('sell_through_pct')}</th>
    <th class="num" data-col="active_count">Active${arrow('active_count')}</th>
    <th class="num" data-col="sold_count">Sold${arrow('sold_count')}</th>
    <th class="num" data-col="avg_days">Avg Days${arrow('avg_days')}</th>
    <th class="num" data-col="avg_price_eur">Avg Price${arrow('avg_price_eur')}</th>
  </tr></thead><tbody>
    ${segments.map(r => {
      const stClass = r.sell_through_pct >= 50 ? 'st-hot' : r.sell_through_pct >= 25 ? 'st-warm' : '';
      return `<tr>
      <td>${esc(r.make)}</td>
      <td>${esc(r.model)}</td>
      <td class="st-cat">${esc(r.generation)}</td>
      <td class="st-cat">${esc(r.fuel)}</td>
      <td class="st-cat">${esc(r.mileage)}</td>
      <td class="st-cat">${esc(r.body)}</td>
      <td class="num ${stClass}"><strong>${r.sell_through_pct}%</strong></td>
      <td class="num">${fmtNum(r.active_count)}</td>
      <td class="num">${fmtNum(r.sold_count)}</td>
      <td class="num">${r.avg_days ?? 'â€”'}</td>
      <td class="num">${r.avg_price_eur ? fmtNum(r.avg_price_eur) + ' â‚¬' : 'â€”'}</td>
    </tr>`;}).join('')}
  </tbody></table>`;
}

function wireStControls() {
  $$('.st-time-btn').forEach(b => b.onclick = () => {
    _stTimeWindow = parseInt(b.dataset.tw);
    renderSellthrough();
  });
  const minEl = document.getElementById('st_min_n');
  if (minEl) minEl.onchange = () => {
    _stMinN = Math.max(1, parseInt(minEl.value) || 5);
    renderSellthrough();
  };
}

function wireStSorting() {
  $$('.st-tbl th[data-col]').forEach(th => {
    th.onclick = () => {
      const col = th.dataset.col;
      if (_stSort.col === col) _stSort.dir = _stSort.dir === 'desc' ? 'asc' : 'desc';
      else { _stSort.col = col; _stSort.dir = 'desc'; }
      const dir = _stSort.dir === 'asc' ? 1 : -1;
      _stSegments.sort((a, b) => {
        const va = a[col], vb = b[col];
        if (va == null && vb == null) return 0;
        if (va == null) return 1;
        if (vb == null) return -1;
        if (typeof va === 'string') return dir * va.localeCompare(vb);
        return dir * (va - vb);
      });
      const wrap = document.getElementById('stTableWrap');
      if (wrap) wrap.innerHTML = stSegmentTable(_stSegments);
      wireStSorting();
    };
  });
}
```

### [2026-05-27 20:03] 999 CarScrapper\web\static\style.css
**Change**: (fill in — what changed and why)
**Old value**:
```css
/* ---- Sell-through tab ---- */
.st-header {
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 12px; margin-bottom: 16px;
}
.st-header h2 { margin: 0; font-size: 18px; }
.st-controls { display: flex; align-items: end; gap: 16px; flex-wrap: wrap; }
.st-meta { font-size: 12px; color: var(--muted); align-self: center; }
.st-field { display: flex; flex-direction: column; gap: 3px; }
.st-field > span { font-size: 10px; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: .5px; }
.st-input { background: var(--bg); border: 1px solid var(--border); color: var(--text);
  border-radius: var(--radius); padding: 5px 8px; font-size: 13px; }
.st-input.small { width: 55px; }
.st-seg { display: flex; }
.st-time-btn {
  background: var(--bg); border: 1px solid var(--border); color: var(--muted);
  padding: 5px 10px; font-size: 12px; cursor: pointer; transition: .15s;
}
.st-seg .st-time-btn:first-child { border-radius: var(--radius) 0 0 var(--radius); }
.st-seg .st-time-btn:last-child { border-radius: 0 var(--radius) var(--radius) 0; }
.st-seg .st-time-btn:not(:first-child) { border-left: 0; }
.st-time-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.st-tbl-scroll { max-height: 75vh; overflow-y: auto; border: 1px solid var(--border); border-radius: var(--radius); }
.st-tbl th[data-col] { cursor: pointer; user-select: none; white-space: nowrap; }
.st-tbl th[data-col]:hover { color: var(--accent); }
.st-tbl thead { position: sticky; top: 0; z-index: 1; }
.st-cat { font-size: 12px; color: var(--muted); }
.st-hot { color: #10b981; }
.st-warm { color: #f59e0b; }
```

### [2026-05-27 20:08] 999 CarScrapper\web\analytics.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    active_rows = conn.execute(f"""
        SELECT make, model, generation, year, engine_type, mileage_km,
               body_type, price_eur
        FROM listings
        WHERE status = 'active' AND {_NOT_BUYER}
          AND make IS NOT NULL AND model IS NOT NULL
    """).fetchall()

    sold_rows = conn.execute(f"""
        SELECT make, model, generation, year, engine_type, mileage_km,
               body_type, price_eur, {DAYS_EXPR} AS days
        FROM listings
        WHERE {REMOVED_FILTER}
          AND make IS NOT NULL AND model IS NOT NULL
          AND COALESCE(removed_at, sold_at) >= datetime('now', ?)
          {cluster_dedup}
    """, (cutoff,)).fetchall()

    def _key(r):
        return (
            r[0],  # make
            r[1],  # model
            _generation_label(r[2], r[3]),  # generation
            r[4] or "Unknown",  # fuel
            _mileage_bucket(r[5]),  # mileage
            r[6] or "Unknown",  # body
        )

    segments: dict[tuple, dict] = defaultdict(lambda: {
        "active": 0, "sold": 0, "days_sum": 0.0, "price_sum": 0.0, "price_n": 0,
    })
    for r in active_rows:
        segments[_key(r)]["active"] += 1
    for r in sold_rows:
        seg = segments[_key(r)]
        seg["sold"] += 1
        if r[8] is not None:
            seg["days_sum"] += r[8]
        if r[7] is not None:
            seg["price_sum"] += r[7]
            seg["price_n"] += 1
```

### [2026-05-27 20:09] 999 CarScrapper\web\static\app.js
**Change**: (fill in — what changed and why)
**Old value**:
```javascript
  const arrow = (col) => _stSort.col === col ? (_stSort.dir === 'asc' ? ' â†‘' : ' â†“') : '';
  return `<table class="st-tbl"><thead><tr>
    <th data-col="make">Make${arrow('make')}</th>
    <th data-col="model">Model${arrow('model')}</th>
    <th data-col="generation">Generation${arrow('generation')}</th>
    <th data-col="fuel">Fuel${arrow('fuel')}</th>
    <th data-col="mileage">Mileage${arrow('mileage')}</th>
    <th data-col="body">Body${arrow('body')}</th>
    <th class="num" data-col="sell_through_pct">Sell-through${arrow('sell_through_pct')}</th>
    <th class="num" data-col="active_count">Active${arrow('active_count')}</th>
    <th class="num" data-col="sold_count">Sold${arrow('sold_count')}</th>
    <th class="num" data-col="avg_days">Avg Days${arrow('avg_days')}</th>
    <th class="num" data-col="avg_price_eur">Avg Price${arrow('avg_price_eur')}</th>
  </tr></thead><tbody>
    ${segments.map((r, i) => {
      const stClass = r.sell_through_pct >= 50 ? 'st-hot' : r.sell_through_pct >= 25 ? 'st-warm' : '';
      return `<tr>
      <td><strong>${esc(r.make)}</strong></td>
      <td><strong>${esc(r.model)}</strong></td>
      <td>${esc(r.generation)}</td>
      <td>${esc(r.fuel)}</td>
      <td>${esc(r.mileage)}</td>
      <td>${esc(r.body)}</td>
```

### [2026-05-27 20:21] 999 CarScrapper\web\analytics.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
def sell_through_segments(
    conn: sqlite3.Connection,
    time_window: int = 90,
) -> list[dict]:
    """Ranked sell-through by every combo of (make, model, generation, fuel, mileage, body).

    Uses cluster dedup only (newest per car_identity) â€” does NOT exclude
    relisted cars, because a removal + relist is still a sell event for
    sell-through purposes.
    """
    cluster_dedup = _cluster_dedup_sql()
    cutoff = f"-{int(time_window)} days"

    active_rows = conn.execute(f"""
        SELECT make, model, year, engine_type, mileage_km,
               body_type, price_eur
        FROM listings
        WHERE status = 'active' AND {_NOT_BUYER}
          AND make IS NOT NULL AND model IS NOT NULL
    """).fetchall()

    sold_rows = conn.execute(f"""
        SELECT make, model, year, engine_type, mileage_km,
               body_type, price_eur, {DAYS_EXPR} AS days
        FROM listings
        WHERE {REMOVED_FILTER}
          AND make IS NOT NULL AND model IS NOT NULL
          AND COALESCE(removed_at, sold_at) >= datetime('now', ?)
          {cluster_dedup}
    """, (cutoff,)).fetchall()

    def _key(r):
        return (
            r[0],  # make
            r[1],  # model
            _year_bucket(r[2]) if r[2] else "Unknown",  # years
            r[3] or "Unknown",  # fuel
            _mileage_bucket(r[4]),  # mileage
            r[5] or "Unknown",  # body
        )

    segments: dict[tuple, dict] = defaultdict(lambda: {
        "active": 0, "sold": 0, "days_sum": 0.0, "price_sum": 0.0, "price_n": 0,
    })
    for r in active_rows:
        segments[_key(r)]["active"] += 1
    for r in sold_rows:
        seg = segments[_key(r)]
        seg["sold"] += 1
        if r[7] is not None:
            seg["days_sum"] += r[7]
        if r[6] is not None:
            seg["price_sum"] += r[6]
            seg["price_n"] += 1

    MIN_N = 5
    out = []
    for (make, model, years, fuel, km, body), seg in segments.items():
        total = seg["active"] + seg["sold"]
        if total < MIN_N:
            continue
        st = round(100.0 * seg["sold"] / total, 1) if total else 0.0
        avg_d = round(seg["days_sum"] / seg["sold"], 1) if seg["sold"] else None
        avg_p = int(seg["price_sum"] / seg["price_n"]) if seg["price_n"] else None
        out.append({
            "make": make, "model": model, "years": years,
            "fuel": fuel, "mileage": km, "body": body,
            "sell_through_pct": st, "active_count": seg["active"],
            "sold_count": seg["sold"], "avg_days": avg_d,
            "avg_price_eur": avg_p, "total_n": total,
        })
    out.sort(key=lambda x: (-x["sell_through_pct"], -x["total_n"]))
    return out
```

### [2026-05-27 20:21] 999 CarScrapper\web\static\app.js
**Change**: (fill in — what changed and why)
**Old value**:
```javascript
    <th data-col="years">Years${arrow('years')}</th>
    <th data-col="fuel">Fuel${arrow('fuel')}</th>
    <th data-col="mileage">Mileage${arrow('mileage')}</th>
    <th data-col="body">Body${arrow('body')}</th>
    <th class="num" data-col="sell_through_pct">Sell-through${arrow('sell_through_pct')}</th>
```

### [2026-05-27 20:27] 999 CarScrapper\web\static\app.js
**Change**: (fill in — what changed and why)
**Old value**:
```javascript
/* ---------------- sell-through tab ---------------- */
let _stSegments = [];
let _stSort = { col: 'sell_through_pct', dir: 'desc' };
let _stTimeWindow = 90;

async function renderSellthrough() {
  const host = $('#sellthroughContent');
  host.innerHTML = '<div class="st-loading">Loading sell-through data...</div>';
  try {
    const segments = await api(`/api/analytics/sell_through_segments?time_window=${_stTimeWindow}`);
    _stSegments = segments;
    _stSort = { col: 'sell_through_pct', dir: 'desc' };

    host.innerHTML = `
      <div class="st-header">
        <div>
          <h2>Top Sell-through Rates</h2>
          <p class="st-sub">${fmtNum(segments.length)} car segments ranked by how fast they sell (last ${_stTimeWindow} days)</p>
        </div>
        <div class="st-seg">
          ${[30,60,90,180].map(v => `<button class="st-time-btn${_stTimeWindow === v ? ' active' : ''}" data-tw="${v}">${v}d</button>`).join('')}
        </div>
      </div>
      <div class="st-tbl-scroll" id="stTableWrap">${stSegmentTable(segments)}</div>`;
    $$('.st-time-btn').forEach(b => b.onclick = () => {
      _stTimeWindow = parseInt(b.dataset.tw);
      renderSellthrough();
    });
    wireStSorting();
  } catch (e) {
    host.innerHTML = `<div class="empty">Error: ${esc(e.message)}</div>`;
  }
}
```

### [2026-05-27 20:27] 999 CarScrapper\web\static\style.css
**Change**: (fill in — what changed and why)
**Old value**:
```css
.st-hot { color: #10b981; font-size: 15px; }
.st-warm { color: #f59e0b; font-size: 15px; }
```

### [2026-05-27 21:29] 999 CarScrapper\db\database.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
```

### [2026-05-28 15:43] ASP Scrapper\app.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    "interval_minutes": 5,
    "target_months": ["aprilie"],
}
```

### [2026-05-28 15:55] ASP Scrapper\app.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
RO_MONTHS = [
    "ianuarie", "februarie", "martie", "aprilie", "mai", "iunie",
    "iulie", "august", "septembrie", "octombrie", "noiembrie", "decembrie"
]
```

### [2026-05-28 16:53] 999 CarScrapper\pipeline.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    shard: Optional[tuple[int, int]] = None,
    fast: bool = True,
    refresh_older_than_hours: Optional[float] = None,
) -> dict:
```

### [2026-05-28 16:56] 999 CarScrapper\scheduler_f.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
"""Schedule F â€” 24/7 production scheduler.

Picked by `scripts/schedule_sim.py` as the best variant across coverage,
latency, price-change capture, and 999.md request load.

Jobs:
  tick     every 10 min     GraphQL discovery + immediate detail-fetch of new IDs
  incr     10:00 + 18:00    refresh listings whose detail is >12h stale (price drift)
  full     Sun 04:00        full discovery + reconciliation + verify_sold + backup
```

### [2026-05-28 17:04] 999 CarScrapper\pipeline.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    shard: Optional[tuple[int, int]] = None,
    fast: bool = True,
    refresh_older_than_hours: Optional[float] = None,
    skip_discovery: bool = False,
    skip_backup: bool = False,
) -> dict:
```

### [2026-05-28 17:06] 999 CarScrapper\refresher_loop.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
"""Continuous price/spec refresher.

Loops `pipeline.run(refresh_known=True)` back-to-back, forever. Pairs with
scheduler_f.py which handles new-listing discovery on a separate cadence.

What this DOES:
  - Pulls all active listing IDs from the local DB.
  - Re-fetches each listing's detail HTML (no photos — refresh=True path).
  - Updates price / mileage / description / spec changes.

What this SKIPS (delegated to scheduler_f.py):
  - GraphQL discovery crawl (~1,000+ pages — the big save).
  - verify-sold for missing IDs.
  - Pre-run DB backup (would otherwise fire every loop iteration).

Run:
    python refresher_loop.py

Recommended deployment: same machine as scheduler_f.py. SQLite WAL handles
concurrent writers; the two processes coordinate via the DB only.
"""
from __future__ import annotations

import asyncio
import gc
import signal
import sys
import time
from pathlib import Path

from loguru import logger

import config
from pipeline import run

# ─── Tunables ────────────────────────────────────────────────────────────────
PAUSE_BETWEEN_LOOPS_SEC = 30    # short breather so a hot loop doesn't peg the
                                # site if the active set is small
JOB_TIMEOUT_SEC = 6 * 60 * 60   # 6h ceiling per pass — if it runs longer, abort
                                # and start fresh (avoids zombie pass)

LOG_DIR = config.DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

_shutdown = False


def _request_shutdown(signum, _frame) -> None:
    global _shutdown
    logger.warning(f"signal {signum} received — finishing this pass then exiting")
    _shutdown = True


def _setup_logging() -> None:
    logger.remove()
    logger.add(sys.stderr, level="INFO",
               format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | refresher | {message}")
    logger.add(str(LOG_DIR / "refresher_loop_{time:YYYY-MM-DD}.log"),
               rotation="50 MB", retention="14 days", compression="gz",
               level="INFO",
               format="{time:YYYY-MM-DD HH:mm:ss} | {level: <7} | {message}")


def main() -> None:
    _setup_logging()
    signal.signal(signal.SIGINT, _request_shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _request_shutdown)

    logger.info("refresher_loop online — looping refresh_known passes")
    pass_n = 0
    while not _shutdown:
        pass_n += 1
        t0 = time.monotonic()
        logger.info(f"=== pass #{pass_n} start ===")
        try:
            asyncio.run(asyncio.wait_for(
                run(
                    mode="full",
                    refresh_known=True,
                    fast=True,
                    skip_discovery=True,    # scheduler_f handles GraphQL crawl
                    skip_backup=True,       # don't backup every ~30 min
                ),
                timeout=JOB_TIMEOUT_SEC,
            ))
        except asyncio.TimeoutError:
            logger.error(f"pass #{pass_n}: TIMEOUT after {JOB_TIMEOUT_SEC}s — aborted")
        except Exception as e:  # noqa: BLE001
            logger.exception(f"pass #{pass_n}: failed with {type(e).__name__}: {e}")
        finally:
            gc.collect()
            dt = time.monotonic() - t0
            logger.info(f"=== pass #{pass_n} done in {dt:.1f}s ===")

        if _shutdown:
            break
        # Short pause so a very-fast loop doesn't hammer the site if active
        # set is tiny. Sleep in 1-sec chunks so SIGTERM is responsive.
        for _ in range(PAUSE_BETWEEN_LOOPS_SEC):
            if _shutdown:
                break
            time.sleep(1)

    logger.info("refresher_loop exited cleanly")


if __name__ == "__main__":
    main()
```

### [2026-05-28 17:11] 999 CarScrapper\config.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
SCRAPE_CHUNK_SIZE = 500
```

### [2026-05-28 17:12] 999 CarScrapper\pipeline.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    def make_worker(session: Session):
        async def worker(lid: int, is_new: bool):
            try:
                data, photos = await scrape_one(session, lid, refresh=not is_new)
                if not data:
                    stats["errors"] += 1  # CPython dict update is atomic under the GIL
                    return
                # Stub on a refresh = listing deleted mid-run. Soft-archive instead
                # of nuking real price/spec data with NULLs. (For NEW we just skip:
                # there's nothing to preserve, and inserting an empty row is noise.)
                if _is_stub(data):
                    if not is_new:
                        with db.connect() as conn:
                            _soft_archive(conn, lid)
                        stats["listings_removed"] += 1
                        progress["done"] += 1
                        logger.info(f"[{progress['done']:5d}/{total_targets}] DEL {lid} (deleted mid-run)")
                    else:
                        stats["errors"] += 1
                    return
                # No global lock: SQLite WAL handles writer serialization itself,
                # and CPython int += is atomic. The previous `async with sem_lock`
                # turned 16 concurrent workers into 1 effective worker.
                with db.connect() as conn:
                    if is_new:
                        db.insert_listing(conn, data)
                        if photos:
                            db.insert_photos(conn, lid, photos)
                            stats["photos_downloaded"] += len(photos)
                            # Cluster detection: does this new listing's
                            # photo set match an existing listing's? If yes,
                            # join its car_identity cluster (relisted car).
                            try:
                                prior = db.find_cluster_for_photos(
                                    conn, photos, lid,
                                    new_make=data.get("make"),
                                    new_model=data.get("model"),
                                )
                                db.assign_cluster(conn, lid, prior)
                                if prior is not None:
                                    stats.setdefault("relisted_matched", 0)
                                    stats["relisted_matched"] += 1
                                    logger.info(f"  [cluster] {lid} = relist of {prior}")
                            except Exception as ce:  # noqa: BLE001
                                logger.warning(f"cluster check failed for {lid}: {ce}")
                        else:
                            # No photos â†’ singleton cluster so cluster_id is set.
                            try:
                                db.assign_cluster(conn, lid, None)
                            except Exception:
                                pass
                        stats["listings_new"] += 1
                        tag = "NEW"
                    else:
                        db.update_listing(conn, data)
                        stats["listings_updated"] += 1
                        tag = "upd"
                progress["done"] += 1
```

### [2026-05-28 17:24] 999 CarScrapper\pipeline.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    shard: Optional[tuple[int, int]] = None,
    fast: bool = True,
    refresh_older_than_hours: Optional[float] = None,
) -> dict:
```

### [2026-05-28 17:26] 999 CarScrapper\refresher_loop.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
"""Continuous refresher â€” loops `python pipeline.py --mode full --refresh-known`.

Identical behavior to the standalone command: discovery, verify-sold, refresh
every known active listing. Runs back-to-back forever with a short pause.

Run:
    python refresher_loop.py
"""
```

### [2026-05-28 17:58] 999 CarScrapper\pipeline.py
**Change**: (fill in — what changed and why)
**Old value**:
```python
    def make_worker(session: Session, conn):
        async def worker(lid: int, is_new: bool):
            try:
                data, photos = await scrape_one(session, lid, refresh=not is_new)
                if not data:
                    stats["errors"] += 1  # CPython dict update is atomic under the GIL
                    return
                # Stub on a refresh = listing deleted mid-run. Soft-archive instead
                # of nuking real price/spec data with NULLs. (For NEW we just skip:
                # there's nothing to preserve, and inserting an empty row is noise.)
                if _is_stub(data):
                    if not is_new:
                        _soft_archive(conn, lid)
                        stats["listings_removed"] += 1
                        progress["done"] += 1
                        logger.info(f"[{progress['done']:5d}/{total_targets}] DEL {lid} (deleted mid-run)")
                    else:
                        stats["errors"] += 1
                    return
                # Shared per-chunk connection: workers run on a single event loop
                # with no awaits between DB statements, so writes can't interleave.
                # Saves ~89k sqlite3.connect/commit/close cycles per refresh pass.
                if is_new:
                    db.insert_listing(conn, data)
```
