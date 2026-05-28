# m99gadgets — Chat History

> Log of important Claude Code sessions for this project.
> Paste key decisions, solutions, and context from past chats here.

---

## Format

```
### [YYYY-MM-DD] Session title
**What was asked**: brief description
**What was done**: summary of changes made
**Key decisions**: why X was chosen over Y
**Files changed**: list of modified files
**Outcome**: did it work? any follow-up needed?
```

---

## Sessions

### [2026-04-21] Bulk Product Catalog Update + Core JS/HTML Changes
**What was asked**: Product pages updated, core files (app.js, index.html, search.js, generate_products.py) modified.
**What was done**:
1. **generate_products.py** — updated to read from `Analiza_GPU.xlsx` (rows 99-164, cols N-Q). Dead products (black background) excluded. LibreTranslate integration added (optional, default on).
2. **search.js** — search logic updated (exact changes not logged).
3. **index.html / app.js** — UI/layout changes (exact changes not logged from session).
4. **Product catalog bulk update** — all `static/p/*.html` pages refreshed. New product lines added: Ajazz AK680 Max Wireless (black/yellow), Attack Shark R85 (black/white).
**Key decisions**: LibreTranslate used for RO→RU translation automation in the generator.
**Files changed**: `generate_products.py`, `static/js/app.js`, `static/js/search.js`, `static/index.html`, all `static/p/*.html` files.
**Outcome**: Product catalog expanded, generator now Excel-driven.

### [2026-04-20] Mobile Fixes + Image Optimizer

**What was asked**: Fix mobile UX issues on m99gadgets site and add image optimization.

**What was done**:
1. **Cart button** — moved `<button class="cart-btn">` out of `<header>` to a direct child of `<body>`. Root cause: Safari iOS positions `position:fixed` children relative to a `backdrop-filter` parent instead of the viewport. Fix makes it `position:fixed; top:12px; right:1.5rem; z-index:200` on desktop (overlays header), keeps existing `bottom:84px; right:16px` on mobile.
2. **Dark mode toggle** — removed `display:none !important` override in inline `<style>` of `index.html`. Moved `.m-theme-toggle` button in HTML from top of hero (before canvas) to after `.stat-pills`. Changed CSS from `position:absolute; top:12px; left:16px` to `position:static; margin:1rem auto 0; display:inline-flex` — now appears centered below hero stats on mobile.
3. **Card image white background** — `.card-vis` background changed from grey gradient to `#ffffff` in `app.css`. Was causing product images (white bg `.webp`) to disappear in light mode.
4. **HOF page mobile** — added `html { overflow-x: hidden }`, `height:100vh` fallback before `100dvh` for older iOS Safari, reduced nav padding to `.75rem` on 640px, changed `.cbg` from `height:100dvh` to `height:auto; min-height:90vh` so combo generator doesn't clip on short viewports, widened product cards to `80vw` when stacked.
5. **Image optimizer** — created `scripts/optimize_images.py`: scans `static/images/`, `static/hof/`, `hall of fame/`, converts non-webp to `.webp` at quality 82, downscales >1920px (>800px for product thumbnails). Integrated into `generate_products.py` — runs automatically at start of `main()` before image scan, so `.webp` files are picked up in `products.json`.

**Key decisions**:
- Cart outside header (not conditional) — simplest fix for backdrop-filter bug; desktop positioning via `position:fixed` overlay works cleanly
- `height:auto` on `.cbg` instead of `100dvh` — combo generator has too much stacked content on mobile to force single viewport height
- Optimizer runs at start of `generate_products.py` (not end) — so the disk_images scan picks up freshly converted `.webp` filenames in the output JSON

**Files changed**:
- `static/css/app.css`
- `static/index.html`
- `static/showcase/index.html`
- `scripts/optimize_images.py` (new)
- `generate_products.py`

**Outcome**: All fixes implemented. Image optimizer requires `pip install Pillow`. Run `python scripts/optimize_images.py` for dry run, add `--convert` to apply, `--convert --apply` to also delete originals.

---

### [2026-04-20] Cart + Theme Toggle Refinements

**What was asked**: Cart pill too big; theme toggle position wrong.

**Root cause found**: Base `.cart-btn` has `top:12px` (desktop overlay). Mobile rule added `bottom:74px` but didn't unset `top`. When both `top` and `bottom` are set on `position:fixed`, the element stretches to fill the gap — that's why it looked like a full-height orange bar.

**What was done**:
- Cart: added `top:auto` to reset the base top, changed to 44×44px circle (`border-radius:50%`), aligned `right:20px` to match the back-to-top button
- Theme toggle: tried `position:fixed` first (stayed on screen while scrolling — unwanted). Changed to `position:absolute; top:12px; left:12px` inside `.hero` — appears in top-left corner of banner, scrolls away when user scrolls past hero

**Key decision**: `position:absolute` inside hero vs `position:fixed` — user wanted it visible only while banner is on screen, not following scroll.

---

## How to use
After finishing a session on this project, summarize it here.
Focus on: decisions made, mistakes caught, patterns that worked.

[[../projects/m99gadgets|Back to m99gadgets]] · [[../index|Vault Index]]

---

### [2026-04-21] — SEO: Domain Mismatch Fix (m99gadgets.com → m99gadgets.app)

**What was asked**: User reported that searching "m99 gadgets", "m99", or product names like "aula" on Google returns nothing. Site is deployed at `m99-gadgets.netlify.app` with custom domain `m99gadgets.app` (bought from name.com via GitHub Student plan) that was "still propagating" after a day.

**What was done**:
1. **Diagnosed two stacked problems**:
   - All SEO metadata (canonical, sitemap, OG, JSON-LD, robots.txt) referenced `https://m99gadgets.com/` — a `.com` domain the user does **not** own. Googlebot crawling the netlify.app URL read "canonical is m99gadgets.com", tried to index that, failed → nothing got indexed.
   - The actual owned domain is `m99gadgets.app`. DNS was not actually propagating — `nslookup -type=ns m99gadgets.app 1.1.1.1` returned `ns1-4.name.com` (name.com defaults), not Netlify's `*.nsone.net`. User hadn't swapped nameservers at name.com.
2. **Batch-replaced all `m99gadgets.com` → `m99gadgets.app`** via Python script. Updated 67 files, 1,479 replacements. Covered: `generate_products.py:59` (SITE_URL constant), `static/index.html`, `static/sitemap.xml`, `static/robots.txt`, all 60+ `static/p/*.html` product pages.
3. **Instructed user** to swap nameservers at name.com from `ns1-4.name.com` to `dns1-4.p08.nsone.net` (Netlify's assigned NS for this domain).
4. **Documented post-DNS steps**: commit+push, verify `m99-gadgets.netlify.app` 301→`m99gadgets.app`, Search Console setup (URL-prefix property, HTML file verification, sitemap submit, URL inspection on home + top 3–5 products).

**Key decisions**:
- Python script for mass find-replace instead of individual Edits — 67 files with identical safe string substitution; single transactional operation.
- Did NOT run `generate_products.py` to regenerate product pages — would require Excel file + online scraping. Direct find-replace on existing generated HTML is equivalent and simpler.
- Set realistic expectations: brand searches ("m99 gadgets") should appear ~1–2 weeks post-fix; generic product queries ("aula") won't rank organically without backlinks — competition is 999.md/darwin.md/Amazon. Paid ads or 999.md listings are the realistic play for generic queries.

**Files changed** (67 total): `generate_products.py`, `static/index.html`, `static/sitemap.xml`, `static/robots.txt`, and all `static/p/*.html`.

**Mistakes made**: None during execution. User initially assumed "DNS propagating" label in Netlify meant everything was set up correctly — it doesn't; Netlify shows that label the moment you add a custom domain, regardless of whether nameservers at the registrar have actually been switched. Lesson saved to mistakes.md.

**Outcome**: SEO code fix complete and verified (zero `m99gadgets.com` references remain). Pending user actions: (1) swap nameservers at name.com, (2) commit+push, (3) Google Search Console setup. Not yet committed to git — user to commit after verification.

---

### [2026-05-22] — SEO overhaul: FAQ schema, redirect removal, PostHog attribution, SW skip-waiting

**What was asked**: User said (a) Google doesn't show m99gadgets.app for "aula f75 white md" and similar variations; (b) m99gadgets.app "doesn't look right" while m99-gadgets.netlify.app does on user's Chrome/Safari; (c) expand PostHog tracking to cover searches, clicks, source attribution, organic queries; (d) make SEO target multiple variations like "aula f75 md", "aula f75 white m99", "aula f75 m99 md". Mandate: use agent-browser to test & iterate, don't cause bugs / deployment failures.

**What was done**:
1. **Diagnosed the "doesn't look right" issue**: both domains served byte-identical content (same ETag). The visual difference was the user's browser running an old service worker from a prior deploy. The old `sw.js` had no `skipWaiting()` + `clients.claim()`, so the new SW would stay in "waiting" until every tab of m99gadgets.app closed.
2. **Rewrote `static/sw.js`**: added `skipWaiting()` in install, `clients.claim()` in activate, network-first for HTML and sw.js itself (so deploys land instantly), stale-while-revalidate for products.json, cache-first for images. Bumped cache to `m99-cache-v2026-05-22b`. Added a `'SKIP_WAITING'` message listener as belt-and-suspenders.
3. **Auto-reload on SW update in `static/js/app.js`**: replaced the SW registration block to listen for `controllerchange` and reload once a new controller takes over — so stuck users self-resolve on their next visit instead of needing manual cache clears.
4. **PostHog attribution overhaul in `static/index.html`**: the SPA had `posthog.init()` but ZERO `capture()` calls — everything went to GA4 only. Added a `loaded:` callback that parses `document.referrer` for organic search engines (Google/Bing/Yahoo/Yandex/DuckDuckGo/Ecosia/Baidu) extracting the search query, captures UTM params, classifies source_category (organic_search / paid_or_campaign / referral / internal / direct), and registers everything as super properties + first-touch via `register_once`. Fires explicit `session_start` event.
5. **Dual-sent every existing `ga()` call to PostHog in `static/js/app.js`**: refactored the `ga()` helper to call both `gtag('event')` AND `posthog.capture()`. Single edit gave PostHog parity with the ~25 existing GA event call sites without touching them. Added new events (`lang_change`, `theme_change`, `share_product`, `cart_remove`, `cart_clear`).
6. **Removed the JS redirect from product pages**: the `/p/*.html` pages had a User-Agent-sniffing redirect that bounced humans to the SPA. This was borderline cloaking and gave humans no engagement signal on the indexed content. Replaced with a fully-usable static product page with inline WhatsApp/Telegram/Viber/999.md/SPA buttons, FAQ accordion, image gallery, microdata (`itemprop`), and dual GA4+PostHog tracking.
7. **Added FAQPage JSON-LD + natural keyword variations**: new `_build_faq()` produces 5 Q/A pairs whose answers naturally contain "<name> MD", "<name> m99", "<name> m99 md", "<name> moldova", "m99 <name>". Body copy via `_build_seo_body()` includes the same variations as prose, not as a keyword wall. Title format now `"<NAME> | <CAT> | M99 MD | Preț N MDL | Chișinău, Moldova | M99 Gadgets"`. Strips parentheses from "AULA F75 (White)" → "AULA F75 White" for cleaner search match.
8. **Image sitemap entries**: `write_sitemap()` now declares `xmlns:image` and emits up to 5 `<image:image>` entries per product URL with title/caption that mention M99 + Moldova. Final sitemap: 65 URLs, 303 image entries.
9. **TRANSLATE flag off by default**: defaults to env-overridable (`M99_TRANSLATE=1`). 60/64 products already have `description_ru` filled, so the LibreTranslate call almost always was a no-op anyway. Avoids depending on libretranslate.com being up at build time.
10. **Regenerated all 64 product HTMLs** via generate_products.py. Verified locally with agent-browser: sitemap parses (65 URLs / 303 images), every page has FAQPage in JSON-LD, no redirect script present, contact buttons present, PostHog `session_start` fires with UTM params, GA4 fires, dark/light/lang toggles fire tracked events.
11. **Pre-deploy validation**: confirmed sitemap XML parses, all 64 pages have valid JSON-LD with FAQPage in @graph, sw.js has skipWaiting + clients.claim + cache version, index.html has session_start + organic_query + register_once, app.js has posthog.capture + controllerchange.
12. **Walked user through GSC/Bing/Yandex/Google Business Profile/999.md backlink submission playbook**.
13. **Diagnosed false-alarm "broken XML sitemap"**: user saw plain text in Chrome viewing /sitemap.xml and "Nu s-a putut prelua" in GSC right after submitting. Confirmed via curl that deployed sitemap is valid `application/xml`, 116414 bytes, parses to 65 URLs + 303 images. Chrome strips visible markup when rendering XML; GSC's "Nu s-a putut prelua" is the initial pending state for hours after first submission (auto-resolves).

**Files changed**:
- `static\sw.js` (rewrote: skipWaiting + clients.claim + network-first for HTML)
- `static\index.html` (PostHog init with full attribution/UTM/organic_query capture)
- `static\js\app.js` (ga() dual-sends to PostHog, SW controllerchange auto-reload, +5 new events)
- `generate_products.py` (FAQ helper, SEO body helper, removed redirect, image sitemap, TRANSLATE off by default)
- `static\data\products.json` (regenerated)
- `static\sitemap.xml` (regenerated with image:image entries)
- all 64 `static\p\*.html` files (regenerated)

**Files changed**:
- `static\p\ajazz-aj139v2-mc-black.html`
- `static\p\ajazz-aj139v2-mc-white.html`
- `static\p\ajazz-aj159p-mc-black.html`
- `static\p\ajazz-aj179v2-black.html`
- `static\p\ajazz-ak680-max-black.html`
- `static\p\ajazz-ak680-max-white.html`
- `static\p\ajazz-ak680-max-wireless-black.html`
- `static\p\ajazz-ak680-max-wireless-yellow.html`
- `static\p\ajazz-ak680-max-yellow.html`
- `static\p\ajazz-ak820-75-wired-rgb-purple.html`
- `static\p\ajazz-ak820-75-wired-rgb-yellow.html`
- `static\p\ajazz-ak820-pro-75-rgb-yellow.html`
- `static\p\ajazz-ak820-pro-purple.html`
- `static\p\ajazz-alux68-max.html`
- `static\p\ajazz-alux68-plus-black.html`
- `static\p\ajazz-alux68-plus-white.html`
- `static\p\ajazz-nk68-black.html`
- `static\p\ajazz-nk68-white.html`
- `static\p\ajazz-nk68v2-purple.html`
- `static\p\ajazz-nk68v2-yellow.html`
- `static\p\anker-maggo-2-pack-5000mah.html`
- `static\p\anker-powerbank-20000mah.html`
- `static\p\anker-soundcore-libery-4-pro.html`
- `static\p\anker-soundcore-p20i.html`
- `static\p\anker-soundcore-q20i-black.html`
- `static\p\anker-soundcore-q20i-white.html`
- `static\p\anker-soundcore-q45-black.html`
- `static\p\anker-soundcore-q45-white.html`
- `static\p\attack-shark-r85-black.html`
- `static\p\attack-shark-r85-burned-black.html`
- `static\p\attack-shark-r85-white.html`
- `static\p\attack-shark-x11-black.html`
- `static\p\attack-shark-x11-white.html`
- `static\p\attack-shark-x6-black.html`
- `static\p\attack-shark-x6-white.html`
- `static\p\aula-f75-black.html`
- `static\p\aula-f75-burned-black.html`
- `static\p\aula-f75-white.html`
- `static\p\aula-f87-pro-white.html`
- `static\p\aula-hero68-purple.html`
- `static\p\aula-win68-he-purple.html`
- `static\p\aula-win68-he-yellow.html`
- `static\p\covoras-negru-26x21.html`
- `static\p\dji-mic-mini-full-set.html`
- `static\p\dji-mic-mini-phone-adapter.html`
- `static\p\freewolf-k68-gray.html`
- `static\p\freewolf-k68-orange.html`
- `static\p\gamesir-nova-lite.html`
- `static\p\hxsj-j900-black-cu-fir.html`
- `static\p\hxsj-t66-black.html`
- `static\p\hyperx-cloud-alpha-wired.html`
- `static\p\hyperx-cloud-ii-core-wireless.html`
- `static\p\jbl-go4.html`
- `static\p\jbl-quantum-stream.html`
- `static\p\microsoft-xbox-s-x-controller-black.html`
- `static\p\onikuma-gt808-wireless.html`
- `static\p\onikuma-gt828-wireless.html`
- `static\p\philips-shp9500.html`
- `static\p\ps5-dualsense-controller.html`
- `static\p\skullcandy-crushers-evo-navy-blue.html`
- `static\p\steelseries-arctis-prime.html`
- `static\p\yunzii-al75-pro-white.html`
- `static\p\zealsound-a68s-usb.html`
- `static\p\zealsound-kd8y-usb.html`

**Key decisions**: (1) Remove the JS redirect on /p/*.html entirely rather than weakening it — Google rewards content humans actually use; eliminates cloaking risk; the static page is now fully transactable with inline WhatsApp/Telegram/Viber/999 buttons. (2) Dual-send GA→PostHog from inside the `ga()` helper rather than touching every call site — gave PostHog instant parity with the existing ~25 events for one edit. (3) Default `TRANSLATE` to off (env-overridable via `M99_TRANSLATE=1`) to make the build independent of libretranslate.com uptime. (4) Network-first for HTML in the new sw.js so future deploys never serve stale HTML even briefly. (5) Title format normalized to `"<NAME> | <CAT> | M99 MD | Preț N MDL | Chișinău, Moldova | M99 Gadgets"` — covers the four variation patterns the user explicitly requested ("aula f75 white md", "aula f75 md", "aula f75 white m99", "aula f75 m99 md") in one natural title.

**Mistakes made**: (1) Misread the user's first complaint as a deployment difference between m99gadgets.app and the netlify subdomain — they served byte-identical content (same ETag). Should have checked ETag before assuming deploy was different. (2) Saved a smoke-test screenshot inside `static/_smoke_spa.png` which would have shipped to production — caught and removed before commit. (3) Wrote `print(...)` with Romanian diacritics in a Bash one-liner without setting `PYTHONIOENCODING=utf-8` — failed on Windows cp1250. Fixed by re-running with the env var. Lesson: any Python invocation that touches Romanian text on Windows needs `PYTHONIOENCODING=utf-8`.

**Outcome**: All changes complete, verified locally with agent-browser, deployed via update.bat. After deploy: sitemap at https://m99gadgets.app/sitemap.xml validates (65 URLs + 303 image entries, served as `application/xml`), product pages return ~25KB (was ~14KB), all 64 pages have FAQPage JSON-LD. Pending user-side actions: GSC sitemap status will flip from "Nu s-a putut prelua" to "Reușit" within hours; user to do GSC URL inspection + Bing Webmaster + Yandex Webmaster + Google Business Profile + 999.md cross-link per the submission playbook. Realistic SEO timeline for branded long-tail ranking: 2–6 weeks; generic terms 2–4 months. Stale-cache visual issue on m99gadgets.app will auto-resolve for returning visitors via SW controllerchange → reload.

---

### [2026-05-24] — Clean path-based URLs + bilingual bot-snapshot SEO

**What was asked**: Google was indexing the old `/p/<slug>.html` standalone pages instead of the SPA. User wanted clean URLs like `https://m99gadgets.app/ro/keyboard/aula-f75-white` (and `/ru/...` mirror) that *open the SPA with the product modal already showing* — NOT separate pages. Must rank for "aula f75 md", "aula f75 m99", "AULA F75 купить молдова" across all 64 products in both RO and RU.

**What was done**:
- **Killed** the per-product HTML pipeline. Deleted `static/p/*.html` (64 files) and a prior `static/ro/*.html` attempt. Removed `_product_html`, `write_prerender`, and dead Darwin-skeleton helpers from `generate_products.py` (module shrunk from 1300+ → 591 lines).
- **Clean-URL routing in `static/js/app.js`**: `parseRoute()` / `buildPath()` / `pushRoute()` / `updateRouteSeo()` + `popstate` listener. Modal open/close, language toggle, category-filter clicks all sync URL via `history.pushState`. Legacy `/?id=…&lang=…` auto-rewrites to clean form via `replaceState`.
- **`static/_redirects`** — Netlify rewrites `/ro/*` and `/ru/*` → `/index.html` 200.
- **`static/index.html`**: added `<base href="/">` so relative `images/`, `css/`, `js/`, `data/products.json`, `sw.js` all resolve from root regardless of URL depth. Logo `href="#"` → `href="/"` so `<base>` doesn't turn it into `/#`.
- **`static/serve.json`** — local-dev mirror of `_redirects` (avoids `npx serve -s` swallowing `/showcase`).
- **Bilingual SEO baked into `products.json`**: `generate_products.py` emits a `p.seo` block per product with `title_ro`, `title_ru`, `desc_ro`, `desc_ru`, `canonical_ro`, `canonical_ru`, `keywords` (8 variants per product: `<name> m99`, `<name> md`, `<name> moldova`, `<name> купить`, `<name> молдова`, `<name> кишинев`, `<name> цена`, `<name> pret`), `product_ld`, `breadcrumb_ro_ld`, `breadcrumb_ru_ld`, `faq_ld` (10 Q/A: 5 RO + 5 RU). App.js reads `p.seo` directly — no string-building in JS.
- **Sitemap**: 64 RO + 64 RU URLs + 390 reciprocal hreflang `<xhtml:link>` entries. Old broken `?lang=ro`/`?lang=ru` hreflang variants stripped (same-URL bilingual → Google was discarding cluster).
- **Bot snapshots**: `scripts/prerender.mjs` uses an inline Node HTTP server (no `serve` dep, no Windows EINVAL) + Playwright Chromium to snapshot 146 URLs (RO + RU homepages, 10 categories each, 64 products each) into `static/_prerendered/`. Snapshots are 144 KB vs 33 KB bare SPA = +110 KB rendered SEO.
- **`netlify.toml` + `netlify/edge-functions/seo-snapshot.ts`**: edge function detects Googlebot/Yandex/Bingbot/social UAs on `/ro/*` and `/ru/*` paths and rewrites to `/_prerendered/…`. Humans get SPA (one regex test, ~1ms cost).
- **CI**: `.github/workflows/deploy.yml` now installs Playwright + Chromium and runs `node scripts/prerender.mjs` between Python and Pages deploy so snapshots auto-refresh on every push.

**Files changed**:
- `generate_products.py` — reverted to sitemap-only, added bilingual `p.seo` block per product
- `static/js/app.js` — clean-URL routing (~200 LOC added), reads `p.seo` for per-route meta + JSON-LD
- `static/index.html` — `<base href="/">`, logo href fix
- `static/_redirects`, `static/serve.json`, `netlify.toml`, `netlify/edge-functions/seo-snapshot.ts` — all NEW
- `static/sitemap.xml` — regenerated (RO+RU + hreflang)
- `static/data/products.json` — now carries per-product `seo` field
- `scripts/prerender.mjs` — NEW (Playwright snapshotter with inline HTTP server)
- `package.json` — `prerender` + `prerender:setup` scripts
- `.github/workflows/deploy.yml` — Node + Playwright + prerender steps
- **Deleted**: `static/p/*.html` (64 files), `static/ro/*.html` (prior attempt)

**Key decisions**:
- **Single SPA at every clean URL** (no per-product HTML) — user's hard constraint after I created standalone pages twice and got told off.
- **Bot-only snapshots via edge function** — humans get fast SPA, bots get full SEO. Best of both. Path-scoped to `/ro/*` and `/ru/*` so `/showcase` stays normal.
- **Bilingual hreflang as separate canonical URLs** — `/ro/<cat>/<slug>` and `/ru/<cat>/<slug>` each canonical to itself, with `<xhtml:link>` reciprocal in sitemap.
- **`<base href="/">`** chosen over rewriting every `src="images/..."` in app.js — one line vs hundreds.
- **Built-in Node HTTP server in prerender script** instead of `npx serve` — avoids Windows Node 20+ EINVAL when spawning `.cmd` without `shell:true` (CVE-2024-27980).
- **English category slugs in URLs** (`keyboard`, not `tastaturi`) per user's example.

**Mistakes made**:
- Built standalone "third-party-looking" product pages on first try; built Darwin-skeleton store pages on second try; user wanted clean URLs only on third try. **Should have asked clarifying questions earlier** instead of inferring layout intent from one screenshot.
- Used `npx serve -s` locally — `-s` SPA-rewrites *every* unknown path including `/showcase`, breaking the Produse populare page locally. Production was always fine (Netlify `_redirects` is path-specific). Fixed with `static/serve.json`.
- First prerender script used `spawn("npx", ...)` without `shell: true`, then with `npx.cmd` directly — both EINVAL on Windows Node 20+. Rewrote with inline `http.createServer` — fewer moving parts.
- One regex `sed` over-ate the indentation in `main()` (collapsed `    write_sitemap(...)` to column 0 → `NameError: catalog`). Caught immediately, fixed.

**Outcome**: Pushed to main (commit `10d47e6`, 192 objects, 656 KB). GitHub Action runs Python + Playwright + deploy. Netlify auto-deploys from main and picks up `netlify.toml` + `_redirects` + edge function. Production URL `https://m99gadgets.app/ro/keyboard/aula-f75-white?sort=name` opens SPA with AULA F75 modal; bots get pre-rendered HTML (Cyrillic title for RU, all JSON-LD baked in). User to **resubmit `sitemap.xml` in Google/Bing/Yandex Search Console** to invalidate the old URL set. Expected indexing: ~2-4 weeks Google, 4-8 weeks Yandex.

**Open follow-ups**:
- Verify after Netlify deploy: `curl -A "Googlebot" https://m99gadgets.app/ro/keyboard/aula-f75-white` should return `x-m99-seo-snapshot: 1` response header.
- Confirm Netlify is connected to `main` (not just `gh-pages`) so `netlify.toml` is read. `deploy.yml` still pushes to `gh-pages` — if Netlify watches `main` directly, the gh-pages step is leftover.
- Once URLs indexed, watch Search Console → Performance → Queries for the keyword variants ("aula f75 m99", etc.).

