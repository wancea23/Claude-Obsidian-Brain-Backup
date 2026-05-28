# m99gadgets — Todo & Known Issues

---

## High Priority (post-2026-05-24 clean-URL + bilingual snapshot push)
- [ ] **Watch the GitHub Action** for commit `10d47e6` — new step "Render SEO snapshots for bots" runs Playwright on Ubuntu for the first time. If it fails (Playwright/Chromium install hiccups on CI are common), grab the error from the Actions tab.
- [ ] **Verify Netlify auto-deployed** from `main` after the push — Netlify dashboard → Deploys. Critical: in the latest deploy log search for `seo-snapshot` to confirm the edge function uploaded. If it didn't, Netlify isn't reading `netlify.toml` (means Netlify is pulling from `gh-pages` not `main` — fix by reconnecting Netlify to `main` branch).
- [ ] **Production curl tests** once deploy is green:
  - `curl -sI https://m99gadgets.app/ro/keyboard/aula-f75-white` → 200, content-length ~33 KB (SPA shell, humans)
  - `curl -sI -A "Googlebot" https://m99gadgets.app/ro/keyboard/aula-f75-white` → should include `x-m99-seo-snapshot: 1` (proves edge function fired)
  - `curl -s -A "Googlebot" https://m99gadgets.app/ru/keyboard/aula-f75-white | grep -o "<title>[^<]*</title>"` → Cyrillic title
- [ ] **GSC: remove old sitemap, re-add it** — same URL `https://m99gadgets.app/sitemap.xml` but file contents completely changed (URLs went from `/p/<slug>.html` to `/ro/<cat>/<slug>` + `/ru/<cat>/<slug>`). Removing+re-adding forces re-fetch.
- [ ] **GSC URL Inspection → Request Indexing** for top URLs in BOTH languages: `/ro`, `/ru`, `/ro/keyboard/aula-f75-white`, `/ru/keyboard/aula-f75-white`, `/ro/mouse/attack-shark-x11-white`, etc. (10/day limit per language).
- [ ] **GSC: file a "Removal" request for old `/p/*.html`** URLs (or just rely on 404 — they were deleted, Netlify returns 404, Google de-indexes after recrawl). Faster: temporary URL removal in GSC for the old `/p/*.html` set.
- [ ] **Bing Webmaster**: same sitemap re-submit + URL inspection for ~10 top URLs.
- [ ] **Yandex Webmaster**: re-submit sitemap (critical for RU market). Yandex still reads `<meta name="keywords">` so the per-product `keywords` field in `p.seo` actually helps here.
- [ ] **Rich Results Test** on a sample URL once indexed: https://search.google.com/test/rich-results — paste `https://m99gadgets.app/ro/keyboard/aula-f75-white`. Confirm Product + Breadcrumb + FAQ all parsed.
- [ ] **Google Business Profile** still pending from May session — biggest single ROI for local search.

## Open architectural follow-ups
- [ ] **Reconcile deployment**: `.github/workflows/deploy.yml` pushes to `gh-pages` branch. Live site responds with `Server: Netlify`. Need to confirm whether Netlify pulls from `main` (so `netlify.toml` works) or from `gh-pages` (so `netlify.toml` needs to be in that branch's output). If Netlify is on `main`, the `gh-pages` deploy step is legacy and can be removed.
- [ ] **Snapshot freshness**: `static/_prerendered/` is regenerated on every deploy via the new GH Action step, but if a stock change pushes products.json without re-running Playwright (e.g. if the prerender step fails), snapshots go stale. Add a sanity guard: fail the deploy if `_prerendered/` is older than `products.json`.

## Improvements
- [ ] Add product descriptions to `products_manual.json` for items missing `description` field
- [ ] HOF page: verify combo generator content fits on small screens (375px) without clipping
- [ ] Image optimizer: test full run with `pip install Pillow` then `python scripts/optimize_images.py`
- [ ] Cart `.has-items` class: verify JS adds the class correctly when items added to cart
- [ ] **Run `python scripts/optimize_images.py --convert --apply`** to delete original non-webp files and reclaim ~15-20MB.
- [ ] **Test cart button + theme toggle on real iOS Safari device** to verify backdrop-filter fix.

## Improvements
- [ ] Add product descriptions to `products_manual.json` for items missing `description` field
- [ ] HOF page: verify combo generator content fits on small screens (375px) without clipping
- [ ] Image optimizer: test full run with `pip install Pillow` then `python scripts/optimize_images.py`
- [ ] Cart `.has-items` class: verify JS adds the class correctly when items added to cart

## Nice to Have
- [ ] Add `goal` progress tracking to the HOF page
- [ ] Add `description_ru` (Russian) translations to products_manual.json

## Known Issues
- [x] [2026-05-25] **Fonts not loading on first visit** — SW intercepted cross-origin Google Fonts; fixed by early-return for non-same-origin in sw.js + font preload in index.html
- [x] [2026-05-25] **Scrollbar invisible in dark mode** — thumb was dark-on-dark; added dark-mode overrides + Firefox scrollbar-color

## Completed ✓
- [x] [2026-05-26] **SEO geo-intent rewrite** — titles now "AULA F75 Black - Cumpără în Moldova, 1300 MDL | M99 Gadgets" (was "AULA F75 Black Tastatură - 1300 MDL | M99 Gadgets Moldova"). Meta descs lead with "Cumpără X la N MDL în Chișinău și Moldova (MD)". Russian titles/descs same pattern ("Купить в Молдове / в Кишинёве"). Changed `generate_products.py` + `app.js` fallback. Regenerated `products.json` + `sitemap.xml`. Still need: re-prerender + deploy + Request Indexing on priority URLs.
- [x] [2026-05-24] **Clean URLs + bilingual bot snapshots** — killed per-product HTML, single SPA serves `/ro/<cat>/<slug>` and `/ru/<cat>/<slug>` via Netlify `_redirects`. Path-based routing in `app.js` (pushState on modal/lang/category). Per-product `seo` block in products.json (RO + RU titles/descs/canonical/keywords + Product/Breadcrumb/FAQ JSON-LD). Sitemap = 64 RO + 64 RU + 390 hreflang. `scripts/prerender.mjs` snapshots 146 URLs via Playwright; Netlify Edge Function serves snapshots to bot UAs only. Commit `10d47e6`, pushed to main.
- [x] [2026-05-22] **SEO overhaul v2** — service worker `skipWaiting()` + auto-reload on `controllerchange` (fixes "stale cache makes m99gadgets.app look broken" complaint); removed UA-sniffing JS redirect from `/p/*.html`; added FAQPage JSON-LD with 5 Q/A targeting "<name> md/m99/m99 md/moldova" variations; image sitemap (303 image entries); PostHog dual-send via `ga()` helper + full attribution capture (organic_query, UTM, source_category, first-touch). All 64 product pages regenerated. Title pattern now `"<NAME> | <CAT> | M99 MD | Preț N MDL | Chișinău, Moldova | M99 Gadgets"`.
- [x] [2026-04-21] **DNS** — nameservers swapped at name.com to Netlify's `dns1-4.p08.nsone.net`, m99gadgets.app live.
- [x] [2026-04-21] **Commit + push SEO URL fixes** — 67 files changed (`m99gadgets.com` → `m99gadgets.app`).
- [x] [2026-04-21] **Netlify 301 redirect** from `m99-gadgets.netlify.app` to apex domain.
- [x] [2026-04-21] SEO domain fix — batch-replaced `m99gadgets.com` → `m99gadgets.app` across 67 files (1,479 replacements). Root cause of site not appearing on Google — all canonicals pointed at a domain user didn't own.
- [x] Cart button Safari iOS fix — moved outside `<header>`, now `position:fixed` works correctly
- [x] Mobile theme toggle — `position:absolute` in hero, scrolls away with banner
- [x] Card image white background in light mode — `.card-vis` changed from grey gradient to `#ffffff`
- [x] HOF page mobile overflow — `html { overflow-x:hidden }`, dvh fallback, nav padding
- [x] Image optimizer script — `scripts/optimize_images.py` with auto-run in `generate_products.py`
- [x] Cart circle on mobile — 44×44px circle, `top:auto` bug fixed, aligned with back-to-top button

[[../projects/m99gadgets|← Back to m99gadgets wiki]]
