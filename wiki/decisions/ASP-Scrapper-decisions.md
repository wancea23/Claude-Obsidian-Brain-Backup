# ASP Scrapper — Design Decisions

> WHY things were built the way they are. Add entries as decisions are made.

---

### [2026-05-28] Auto-update appointment design

- **"Better" = strictly earlier date.** Same-day-earlier-hour intentionally NOT rebooked (avoids risky reschedules for marginal gains). Hour comparison was offered but rejected.
- **Current appointment date stored as user-entered config** (Zi/Luna/An GUI entries → `dd.mm.yyyy` string), not auto-fetched. Reason: avoids a my-appointments roundtrip every cycle and avoids parsing the table for the date column. User knows their date; they type it once. After a successful rebook, the in-memory cache updates so we don't loop on the same slot.
- **Target location is a fixed `CTkOptionMenu`**, not free text. Reason: the scrapper only ever inspects two DECA Chișinău locations (`Acad. S. Rădăuțanu, 1` / `Calea Ieșilor, 14`); free text invited typos that would silently never match.
- **New tab in existing browser context** (not new browser, not same page). Reason: keeps cookies/session, doesn't lose the filled scraper form, lets the main check loop continue.
- **Monitor keeps running after success** (vs. stop). Reason: user explicitly chose this — they may want to chase even earlier dates by updating `current_appointment_date` mid-run.
- **3-retry search + 10-reload calendar limits** match the spec verbatim; both fire a TG alert on giving up.
- **Selectors are best-effort from screenshots** for `/APO/my-appointments`: visible-input order (0=IDNP, 1=code, 2=request), button text regex (`C[ĂA]UTARE`, `MODIFIC[ĂA]`, `^DA$`, `PROGRAMEAZ`). DOM was not inspected live — expect tweaks on first real run.
- **Reuses existing `select_date_in_picker`** rather than writing a new picker driver. The Edit/cerere page uses the same Angular `.fod-picker-*` components.

*(No decisions logged yet — add entries during sessions)*

[[../projects/ASP-Scrapper|← Back to ASP Scrapper wiki]] · [[../decisions|← Global Decisions]]
