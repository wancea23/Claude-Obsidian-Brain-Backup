# m99gadgets — Design Decisions

> WHY things were built the way they are. Read before making architectural changes.

---

### [2026-05-24] No per-product HTML files — single SPA serves every clean URL via Netlify rewrites
**Decision**: `/ro/<cat-slug>/<id>` and `/ru/<cat-slug>/<id>` (e.g. `/ro/keyboard/aula-f75-white`) all serve the same `static/index.html`. The SPA's JS reads `window.location.pathname`, applies the language + category filter, and opens the product modal. URL stays clean throughout. **The previous `/p/<slug>.html` per-product page approach was removed entirely.**
**Why**: User explicitly wanted ONE store layout, not separate landing pages competing visually with the modal. With 64 products × 2 languages = 128 URL-distinct surfaces, prerendering separate HTML files was rejected as "creating new pages". Single SPA at every URL keeps the UX consistent and avoids divergent layouts.
**How to apply**:
- `static/_redirects` rewrites `/ro/*` and `/ru/*` to `/index.html` (status 200, not 301 — URL stays).
- `static/serve.json` mirrors this for local `npx serve` (so you don't need `-s` flag, which would also swallow `/showcase`).
- `static/js/app.js` has `parseRoute()` / `buildPath()` / `pushRoute()` / `updateRouteSeo()` + `popstate` listener. Modal open/close, category click, language toggle all sync URL via `history.pushState`.
- For SEO, see the bot-snapshot decision below.

---

### [2026-05-24] SEO via JS injection + Netlify Edge Function bot snapshots — NOT per-page prerender to disk
**Decision**: At runtime, `app.js`'s `updateRouteSeo()` reads `p.seo` from `products.json` and patches `document.title`, meta description, canonical, and injects Product/Breadcrumb/FAQ JSON-LD via `<script type="application/ld+json">`. For bots specifically, `netlify/edge-functions/seo-snapshot.ts` detects Googlebot/Yandex/Bingbot/social UAs and rewrites their `/ro/*` and `/ru/*` requests to `/_prerendered/<path>.html` — fully-rendered snapshots produced by `scripts/prerender.mjs` (Playwright headless Chromium).
**Why**: Modern Googlebot renders JS, so JS-injected meta + JSON-LD works for Google. But Yandex (~15% Moldova/RU search share, important for `m99gadgets.app`) and Bing have weaker JS rendering — they need static HTML. Edge-function UA branching gives bots fully-baked HTML while humans get the snappy SPA (one regex test, ~1ms cost).
**How to apply**:
- Every product needs a `seo` block in `products.json`. `generate_products.py` builds this — see `_build_product_seo()`. Don't string-build SEO in JS; the build step is the source of truth.
- The edge function is path-scoped to `/ro/*` and `/ru/*` ONLY. `/showcase` and other paths bypass it.
- Snapshots regenerate on every deploy via the Playwright step in `.github/workflows/deploy.yml`. If you skip Playwright in CI, bots fall back to the SPA shell (Google fine, Yandex bad).

---

### [2026-05-24] Bilingual hreflang per route — separate canonical URLs for RO and RU, NOT `?lang=` query
**Decision**: `/ro/<cat>/<id>` canonicals to itself; `/ru/<cat>/<id>` canonicals to itself. The sitemap lists both URLs as separate `<url>` entries with reciprocal `<xhtml:link rel="alternate" hreflang="ro|ru|x-default">`. The previous setup that put hreflang variants on `?lang=ro`/`?lang=ru` query strings of a same-URL bilingual page was broken — Google's canonicalization collapses query-string variants to the bare URL, so the hreflang cluster was being discarded.
**Why**: For Google to treat RO and RU as distinct ranking targets, they need distinct canonical URLs. Path-based language (`/ro/`, `/ru/`) is the standard, supported by all crawlers, and lets Yandex index the RU variant cleanly.
**How to apply**: When adding a new language, mirror the path structure (`/de/`, `/fr/`, etc.), add it to `CAT_URL_SLUG` map in both Python and JS, add the language column to `_build_product_seo()`, and re-snapshot.

---

### [2026-05-24] `<base href="/">` in `index.html` — for SPA served at deep clean URLs
**Decision**: `static/index.html` has `<base href="/">` as the first non-meta element in `<head>`. The logo anchor is `href="/"` (not `href="#"`) to avoid `<base>` turning it into a `/#` history-polluter.
**Why**: When the SPA loads at `/ro/keyboard/aula-f75-white`, relative URLs like `<img src="images/foo.webp">`, `fetch('data/products.json')`, `<script src="js/app.js">`, and `navigator.serviceWorker.register('sw.js')` would otherwise resolve to `/ro/keyboard/images/foo.webp` etc. and 404 (or get caught by the SPA rewrite and return HTML). One-line `<base>` fix is much cleaner than rewriting every URL in app.js to be absolute.
**How to apply**: If you add new relative URLs anywhere in the SPA, they automatically resolve from root. Don't remove `<base>` without rewriting every relative URL in the app.

---

### [2026-05-22] Service Worker MUST `skipWaiting()` + `clients.claim()` + auto-reload on `controllerchange`
**Decision**: `sw.js` calls `self.skipWaiting()` in install and `self.clients.claim()` in activate. `app.js` registers a `controllerchange` listener that does `window.location.reload()` once a new SW takes over. Cache name includes the deploy date so caches roll on every release.
**Why**: Before this change, when a new sw.js was deployed, the old SW kept serving cached HTML/CSS/JS to every open tab until **every tab of the domain was closed**. The user complained "m99gadgets.app doesn't look right but m99-gadgets.netlify.app does" — both deploys served byte-identical content (same ETag), but the user's Chrome was stuck on a months-old SW. The visual fix was a deploy plus one auto-reload.
**How to apply**: Any future tweak to sw.js MUST keep both lines. If you ever need a hot-fix SW that does NOT auto-take-over, drop `skipWaiting()` deliberately and explain in the commit. Never remove the controllerchange listener in app.js without a replacement update flow — without it, the SW fix only helps after the user manually closes every tab.

---

### [2026-05-22] Static product pages serve the SAME content to humans and bots — no UA-sniffing redirect
**Decision**: `/p/<slug>.html` is a fully transactable page (WhatsApp/Telegram/Viber/999/SPA buttons inline, full gallery, FAQ accordion, microdata). No JS redirect. The "Vezi în magazin" button is a normal `<a>` link the user can choose to click.
**Why**: The previous template did `if (!isBot) location.replace(spaUrl)` after page load. Google sometimes flags this as cloaking (different content to bots vs humans). More importantly: real visitors NEVER read the static page, so Google has no user engagement signal (dwell time, scroll depth, clicks) for the content it's actually trying to rank. Removing the redirect means the SAME content serves to bots and humans, and Google can collect real engagement data on the indexed URL.
**Alternative considered**: Delay the redirect 3s and offer a "Stay here" button. Rejected — adds complexity; if the content is good enough to keep humans, no redirect is needed at all.
**How to apply**: Never add a UA-sniffing or click-replace redirect to `/p/*.html`. If the SPA gains a feature the static page can't replicate (live stock, chat, etc.), surface it as a CTA link, not an automatic redirect.

---

### [2026-05-22] PostHog gets every event via the existing `ga()` helper, not via parallel `ph()` calls per site
**Decision**: The `ga(name, params)` helper in `app.js` calls BOTH `gtag('event', ...)` AND `posthog.capture(name, ...)` internally. New events that don't make sense in GA4 (attribution snapshots, lang/theme registers) use a separate `ph()` helper. Per-page PostHog init (in `index.html` and in `generate_products.py`'s template) runs an explicit `loaded:` callback that parses `document.referrer`, extracts the organic query from Google/Bing/Yahoo/Yandex/DuckDuckGo/Ecosia/Baidu, captures UTM params, classifies `source_category`, registers everything as super properties + `register_once` first-touch, and fires a `session_start` event.
**Why**: The site already had ~25 `ga(event, params)` call sites for search, cart, contact-click, modal dwell, etc. Migrating each individually to PostHog would have been a huge change set with high regression risk. Dual-send from the helper gave PostHog parity in one edit. Auto-extracting organic_query from `document.referrer` is the only way to know what Google query brought a visitor in (Google strips the `q` param on the destination URL, but it's still on the referrer header — for now).
**How to apply**: When adding a new tracked event, call `ga(name, params)` and it goes to both. Use `ph(name, params)` only for PostHog-specific stuff (attribution, super property registers). Don't add raw `posthog.capture()` calls — they bypass GA and create a coverage gap. Don't add raw `gtag('event', ...)` calls — they bypass PostHog.

---

### [2026-05-22] Generate-time `_keywords()` + `_build_faq()` + `_build_seo_body()` is the canonical place for SEO variations
**Decision**: All keyword/long-tail variations for product pages (e.g. "<name> md", "<name> m99", "<name> m99 md", "<name> moldova", "m99 <name>") are generated in three Python helpers in `generate_products.py`. They produce: (a) the `<meta name="keywords">` string (for Yandex — Google ignores it), (b) 5 FAQ Q/A pairs whose answers naturally contain the variations + FAQPage JSON-LD, (c) prose paragraphs that mention the variations in natural Romanian/Russian sentences.
**Why**: Google penalizes keyword stuffing in meta-only or hidden-text form, but rewards natural prose that contains relevant variations. The FAQ schema gets shown as rich snippets directly in search results. The user's specific request was that ranking works for "aula f75 white md", "aula f75 md", "aula f75 white m99", "aula f75 m99 md" simultaneously — all four are now in the rendered title, h2-seo subtitle, body prose, and FAQ answers.
**How to apply**: To target a new long-tail pattern (e.g. "<name> ieftin"), add the variation to `_keywords()` AND weave it into the natural prose in `_build_seo_body()` or a new FAQ Q/A in `_build_faq()`. Never add a "hidden div" of keywords — that's algorithmic penalty territory. After changing the helpers, run `python generate_products.py` to regenerate all 64 pages + sitemap in one shot.

---

### [2026-05-22] `TRANSLATE` defaults to off; opt in via `M99_TRANSLATE=1`
**Decision**: `generate_products.py` sets `TRANSLATE = (os.environ.get("M99_TRANSLATE", "0").lower() in ("1","true","yes"))` so the build NEVER reaches out to libretranslate.com unless the user explicitly opts in.
**Why**: 60/64 products already have `description_ru` filled from prior runs, so the LibreTranslate call was almost always a no-op anyway. But when the API IS down (it sporadically is), the build would hang or fail for 30+ seconds. Defaulting off makes the build deterministic and offline-capable. User can opt in for new products by setting the env var.
**How to apply**: To translate brand-new products that lack `description_ru`, run `M99_TRANSLATE=1 python generate_products.py` once. Otherwise just `python generate_products.py`.

---

### [2026-04-21] Production domain is `m99gadgets.app`, not `m99gadgets.com`
**Decision**: Site's canonical production domain is `https://m99gadgets.app`. All SEO metadata (canonical, hreflang, OG, JSON-LD, sitemap, robots.txt, `SITE_URL` in `generate_products.py`) must reference `.app`, never `.com`.
**Why**: User bought `m99gadgets.app` from name.com (free via GitHub Student plan). Does NOT own `m99gadgets.com`. The original codebase shipped with `m99gadgets.com` everywhere as a placeholder/intent — Google was reading the canonical, failing to reach `.com`, and deindexing the actual site. Root cause of the "SEO doesn't work" complaint.
**How to apply**: Never re-introduce `m99gadgets.com` anywhere. If regenerating pages via `generate_products.py`, confirm line 59 still says `SITE_URL = "https://m99gadgets.app"`. If ever moving to a different domain, grep-replace across the whole `m99gadgets/` tree (67 files on the last change).

---

### [2026-04-21] DNS on `m99gadgets.app` uses Netlify nameservers, not name.com's
**Decision**: Nameservers at name.com are set to Netlify's `dns1-4.p08.nsone.net`. DNS records (A/CNAME) are managed in Netlify, not name.com.
**Why**: User picked "Netlify DNS" in the Netlify custom-domain flow. That path requires a full NS swap at the registrar — you cannot mix (can't keep name.com NS and also use Netlify DNS). Netlify's "propagating..." label appears the moment you add the domain; it does NOT mean the registrar NS is correct. Always verify via `nslookup -type=ns <domain> 1.1.1.1`.
**How to apply**: If DNS acts up in the future, first check NS with `nslookup -type=ns m99gadgets.app 1.1.1.1` — must return `*.nsone.net`. If it returns `*.name.com`, the NS swap was reverted at the registrar. Do NOT add A records at name.com while Netlify DNS is the intended path.

---

### [2026-04-20] Cart button is a direct `<body>` child, not inside `<header>`
**Decision**: `<button class="cart-btn">` lives outside `<header>`, as a sibling to it.
**Why**: The header has `backdrop-filter: blur(20px)`. Safari iOS repositions `position:fixed` children of backdrop-filter ancestors relative to that element instead of the viewport — cart was invisible/misplaced on mobile Safari.
**Alternative considered**: Keep in header, use JS to detect Safari and reposition dynamically.
**Why rejected**: Fragile, requires UA sniffing. Moving the element is the correct CSS fix.
**CSS**: Base style is `position:fixed; top:12px; right:1.5rem; z-index:200` (desktop overlay). Mobile override is `top:auto; bottom:74px; right:20px; width:44px; height:44px; border-radius:50%`.

---

### [2026-04-20] `.m-theme-toggle` uses `position:absolute` inside `.hero`, not `position:fixed`
**Decision**: Mobile theme toggle is `position:absolute; top:12px; left:12px` inside `.hero`.
**Why**: User wants the toggle visible only while the hero banner is in the viewport. `position:fixed` would make it follow the user while scrolling through the product list.
**Note**: `.hero` has `position:relative; overflow:hidden` — the button sits at top-left corner of the hero and scrolls away with it.

---

### [2026-04-20] `.card-vis` background is `#ffffff` (white), not the original grey gradient
**Decision**: Product image containers always have white background.
**Why**: Product images are `.webp` files with white backgrounds. The original `linear-gradient(160deg,#f8f9fb,#f1f3f6)` grey gradient caused images to blend into the background in light mode — products appeared to have no image. Dark mode already had `background:#ffffff` which is why it only broke in light mode.

---

### [2026-04-20] `optimize_images.py` runs at the START of `generate_products.py`, not the end
**Decision**: Image optimizer runs before the product catalog is built.
**Why**: `generate_products.py` scans `static/images/` for product image files (disk_images scan). Running optimizer first means freshly converted `.webp` files are discovered and listed in `products.json`. Running after would leave old filenames in the JSON for that run.

---

### [2026-04-20] `.cbg` (combo generator section) uses `height:auto` on mobile, not `100dvh`
**Decision**: On mobile (≤640px), `.cbg` is `height:auto; min-height:90vh` instead of `height:100dvh`.
**Why**: The combo generator section has too much stacked content (title, 2 product cards, pricing, CTA) to fit in one mobile viewport height. Forcing `100dvh` would clip content without scroll.

---

### [2026-05-25] Service Worker MUST NOT intercept cross-origin requests (fonts, analytics, CDNs)
**Decision**: `sw.js` fetch handler returns early (`return;` without calling `event.respondWith()`) for any URL that doesn't start with `self.location.origin`. Cross-origin requests (Google Fonts, PostHog, GA, model-viewer CDN) load directly from the network, bypassing the SW entirely.
**Why**: The SW was intercepting Google Fonts CSS/font-file requests via the catch-all "everything else" handler. The SW's `fetch()` for cross-origin font responses didn't cache them, and any timing/network hiccup caused fonts to silently fail. Users saw unstyled text (Bebas Neue → serif fallback, Space Grotesk → sans-serif fallback) on every visit unless they did Ctrl+Shift+R (which bypasses the SW). The same-origin check is the simplest fix with zero downside — the SW has no business caching third-party CDN assets anyway.
**How to apply**: If a future feature needs to cache cross-origin responses (e.g., offline font support), add explicit handling for those specific origins AFTER the early-return guard, using opaque responses. Never let a catch-all handler touch cross-origin requests.

---

### [2026-05-25] Same-origin CSS/JS fetch handler must update cache on success (network-first-then-cache)
**Decision**: The "everything else" handler in `sw.js` now writes successful network responses to the cache (`cache.put(event.request, response.clone())`), not just reads from it on failure.
**Why**: The old handler was network-first but never updated the cache after a successful fetch. The only cached version was from `urlsToCache` at install time. If the network later failed (brief blip, DNS timeout), the fallback was the install-time version — possibly weeks old. Now the fallback is always the most recent successful fetch.
**How to apply**: This is the correct default for same-origin static assets. Don't change it to cache-first (would serve stale CSS/JS). Don't remove the cache-update (would regress the offline fallback).

### [2026-05-26] SEO titles/descriptions rewritten to front-load geo intent — "Cumpără în Moldova" / "Купить в Молдове" first
**Decision**: Product `<title>` changed from `{name} {cat} - {price} MDL | M99 Gadgets Moldova` to `{name} - Cumpără în Moldova, {price} MDL | M99 Gadgets`. Meta description changed from `{name} {cat} {brand} în Moldova (MD) la M99 Gadgets. Preț: {price} MDL.` to `Cumpără {name} la {price} MDL în Chișinău și Moldova (MD).` Same pattern in Russian: "Купить в Молдове" / "в Кишинёве и Молдове". Applied in `generate_products.py` (source of truth) and `app.js` (fallback).
**Why**: Site ranked for branded queries ("aula f75 m99") but NOT for geo queries ("aula f75 md"). Competitor `pestore.online` (same low authority, `.online` TLD) outranked us because their title said "Купить в Кишинёве, Молдова" — explicit geo intent. Google was reading "M99 Gadgets Moldova" as a brand name, not a geo signal. The fix front-loads buying intent + geo terms so Google matches "product md" and "product moldova" queries.
**How to apply**: After changing title/desc templates in `generate_products.py`, run `python generate_products.py` to regenerate `products.json` + `sitemap.xml`, then re-prerender (`node scripts/prerender.mjs`) and redeploy. Don't resubmit the sitemap in GSC — just "Request Indexing" on 5-6 key URLs. Google recrawls the rest on its own cycle.

---

### [2026-05-26] After SEO template changes: Request Indexing per-URL, do NOT resubmit sitemap
**Decision**: When title/description templates change but the sitemap URL structure stays the same, use GSC "URL Inspection → Request Indexing" on priority pages. Do NOT click "Resubmit" on the sitemap.
**Why**: The 27 already-indexed pages keep their indexing stats. Resubmitting can reset crawl stats and doesn't speed up re-indexing anyway. Per-URL Request Indexing is the fastest path (recrawl within hours). Same applies to Bing (URL Submission) and Yandex (Reindex URL).
**How to apply**: After deploy, open GSC → URL Inspection → paste URL → Request Indexing. Do ~5-6 priority product pages. Repeat in Bing Webmaster and Yandex Webmaster.

---

[[../projects/m99gadgets|← Back to m99gadgets wiki]] · [[../decisions|← Global Decisions]]
