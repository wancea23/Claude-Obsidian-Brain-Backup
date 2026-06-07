# m99gadgets

> Premium gadget e-commerce store · Flip-card product grid · Bilingual (RO/RU)
> **Last synced**: 2026-06-07 18:48

**Path**: `Code/m99gadgets/`
**Stack**: HTML, JavaScript, JSON, Python, Markdown
**Language**: Romanian (primary) + English toggle
**Analytics**: Google Analytics 4 (`G-2F5F9VF4N5`)
**Platform**: Static site — runs in browser, no backend
**Production domain**: `https://m99gadgets.app` (registrar: name.com via GitHub Student, DNS via Netlify `dns1-4.p08.nsone.net`)
**Netlify subdomain**: `m99-gadgets.netlify.app` (301 → primary domain)

---

## What It Does

### User Experience
- Dark hero section with large "M99" watermark + animated orange accent
- Product cards that **flip on click** — front shows image/price, back shows full description
- Promo banner (animated pulse pills)
- Cart drawer (slides in from top-right, bottom sheet on mobile)
- Search + filter bar (price range, category)
- Language toggle RO/EN
- Dark/light mode auto-detected from system preference, stored in localStorage
- `showcase/` — product image gallery (`.webp` format)
- Service Worker (`sw.js`) — offline support / PWA

### System Experience
- `static/index.html` — full app (single HTML file with inline `<style>` + external `app.css`)
- `static/css/app.css` — main design system (CSS custom properties)
- `static/js/` — JS modules
- `static/data/` — product JSON data
- `static/images/` — product images (`.webp`)
- `static/showcase/` — showcase gallery images
- `static/hof/` — Hall of Fame section
- `generate_products.py` — Python script that builds product data JSON + auto-triggers image optimizer
- `scripts/optimize_images.py` — converts non-webp images to `.webp` at quality 82; runs on every generate_products.py call
- `models/` — 3D model assets
- `update.bat` — rebuild trigger
- `package.json` — Node.js project config, npm scripts, dependencies
- `hall of fame/` — root-level HOF section assets (separate from `static/hof/`)
- `scripts/` — root-level build/utility scripts (separate from `static/js/`)

---

## Design System

### Color Palette (CSS Custom Properties)
```css
:root {
  --bg:           #f2f1ed;   /* warm off-white page bg */
  --surface:      #ffffff;   /* card / panel surface */
  --surface-hi:   #fafaf8;   /* slightly elevated surface */
  --warm:         #f7f6f2;   /* warm tint bg */
  --ink:          #0f1117;   /* primary text */
  --ink2:         #374151;   /* secondary text */
  --muted:        #6b7280;   /* placeholder / meta text */
  --border:       rgba(17,24,39,.07);
  --border-s:     rgba(17,24,39,.11);

  --accent:       #fe5000;   /* orange — CTA, price, logo, active states */
  --accent-hover: #e8490a;
  --accent-subtle:rgba(254,80,0,0.07);

  --green:  #059669;  --gl: #dcf5ec;    /* in-stock / positive */
  --amber:  #d97706;  --al: #fef0c7;    /* warning */
  --red:    #dc2626;  --rl: #fce8e8;    /* out of stock / error */
  --blue:   #2563eb;  --bl: #dceafe;    /* info */

  --shadow-sm: 0 1px 2px rgba(17,24,39,0.04), 0 4px 16px rgba(17,24,39,0.06);
  --shadow-md: 0 2px 4px rgba(17,24,39,0.04), 0 12px 32px rgba(17,24,39,0.09);
  --shadow-lg: 0 4px 8px rgba(17,24,39,0.05), 0 24px 56px rgba(17,24,39,0.13);
  --shadow-glow: 0 4px 16px rgba(254,80,0,0.35), 0 2px 4px rgba(254,80,0,0.2);
}
```

### Dark Mode
Toggled via `<html class="dark">`. System preference auto-applied on load.
```js
if (localStorage.getItem('theme') === 'dark' || 
    (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
  document.documentElement.classList.add('dark');
}
```

### Typography
```
Headings:   'Bebas Neue' — display, all-caps, large tracking
Body:       'Space Grotesk' — modern geometric sans
Mono/Tech:  'JetBrains Mono' — build pill, code, stats
```

### Motion System
```css
--ease-out:    cubic-bezier(0.16, 1, 0.3, 1)
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1)
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1)   /* bouncy */
--motion-fast: 0.15s
--motion-base: 0.25s
--motion-slow: 0.4s
--motion-flip: 0.6s
```

---

## Signature Components

### Flip Card
```css
/* Card flips on click — front shows product, back shows description */
.card-container { transition: transform 0.4s cubic-bezier(0.175,0.885,0.32,1.275); }
.card-front  { z-index: 2; transform: none; opacity: 1; }
.card-back   {
  position: absolute; top: 0; left: 0;
  transform: perspective(1200px) rotateY(-180deg);
  opacity: 0; visibility: hidden;
  transition: 0.5s cubic-bezier(0.175,0.885,0.32,1.275);
}
/* On flip: front hides, back appears with 3D rotation */
```

### Header (Glassmorphism)
```css
header {
  background: rgba(255,255,255,0.82);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid rgba(17,24,39,0.07);
  box-shadow: 0 1px 0 rgba(17,24,39,0.04), 0 4px 24px rgba(17,24,39,0.04);
  position: sticky; top: 0; z-index: 100;
  animation: headerSlide 0.6s cubic-bezier(0.16,1,0.3,1);
}
```

### Logo Mark
```css
.logo-mark {
  background: linear-gradient(135deg, #ff6820, #fe5000, #d94400);
  background-size: 200% 200%;
  border-radius: 12px;
  animation: logoShine 3s ease infinite;  /* gradient cycles */
  box-shadow: 0 2px 8px rgba(254,80,0,0.3);
}
```

### Hero Section (Dark)
```css
.hero {
  background:
    radial-gradient(ellipse 140% 80% at 50% 110%,
      rgba(254,80,0,0.22) 0%, rgba(254,80,0,0.06) 45%, transparent 65%),
    linear-gradient(180deg, #17171c 0%, #0c0c10 100%);
  /* Giant watermark "M99" text behind everything */
}
.hero::before {
  content: 'M99';
  font-size: 24rem;
  color: transparent;
  -webkit-text-stroke: 1.5px rgba(255,255,255,0.018);
  animation: heroFloatBg 15s ease-in-out infinite alternate;
}
```

### Cart Drawer
```css
.cart-drawer {
  position: fixed; right: 16px; top: 80px;
  width: 360px;
  border-radius: 24px;
  animation: cartIn 0.22s var(--ease-out) forwards;
}
/* Mobile: bottom sheet */
@media(max-width:480px) {
  .cart-drawer { left:0; right:0; bottom:0; top:auto;
    width:100vw; border-radius: 18px 18px 0 0; }
}
```

### Cart Badge (Pulsing)
```css
#cart-count {
  background: var(--accent);
  border-radius: 50%;
  animation: pulseGlow 2s infinite;
}
@keyframes pulseGlow {
  0%   { box-shadow: 0 0 0 0 rgba(254,80,0,0.4); }
  70%  { box-shadow: 0 0 0 6px rgba(254,80,0,0); }
  100% { box-shadow: 0 0 0 0 rgba(254,80,0,0); }
}
```

### Promo Banner Pills
```css
.promo-item {
  background: rgba(254,80,0,0.05);
  border: 1px solid rgba(254,80,0,0.12);
  border-radius: 10px;
  animation: promoPulse 4s ease-in-out infinite alternate;
}
@keyframes promoPulse {
  50% { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.04); }
}
```

### Build Status Pill
```css
.build-pill {
  font-family: 'JetBrains Mono', monospace; font-size: .68rem;
  color: var(--green); background: var(--gl);
  border: 1px solid rgba(16,185,129,.3);
  border-radius: 100px; padding: 5px 12px;
}
.build-dot { animation: blink 1.6s ease-in-out infinite; } /* pulsing green dot */
```

---

## Layout Wireframe
```
┌────────────────────────────────────────────────────────────┐
│ 🔶 M99 Gadgets    [search]  [filters]  🛒  RO/EN  🌙       │  ← sticky glass header
├────────────────────────────────────────────────────────────┤
│  📦 Free delivery  ·  🔒 Secure  ·  ↩ 30-day return       │  ← promo banner (animated)
├────────────────────────────────────────────────────────────┤
│                                                            │
│          M99  ← giant watermark (barely visible)           │
│       [eyebrow label in orange mono]                       │
│       HUGE DISPLAY HEADING (Bebas Neue)                    │
│       subtitle in Space Grotesk                            │
│       [stat pills]                                         │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  [Card][Card][Card][Card]   ← flip cards, min 390px tall   │
│    front: img / name / price                               │
│    back:  full desc / specs / price (revealed on click)    │
├────────────────────────────────────────────────────────────┤
│  Hall of Fame section                                      │
└────────────────────────────────────────────────────────────┘

Cart Drawer (top-right overlay when cart icon clicked):
┌──────────────────────────┐
│ Cart  [×]                │
│ ─────────────────        │
│ Product name    qty +-   │
│ Product name    qty +-   │
│ ─────────────────        │
│ Subtotal: X MDL          │
│ [Clear] [Checkout]       │
└──────────────────────────┘
```

---

## PWA / Service Worker
- `sw.js` registered — enables offline browsing
- Assets cached on install
- Security headers in `_headers` file (Cloudflare/Netlify)

---

## Notes & Gotchas
- Bilingual: `lang-toggle` button switches RO ↔ EN; text stored in JS data
- Card flip uses `perspective(1200px) rotateY` — requires `backface-visibility: hidden` on both faces
- `generate_products.py` reads from **`Analiza_GPU.xlsx`** (rows 99-164, cols N-Q). Dead products (black background rows) are excluded. Merges with `products_manual.json` for price, images, tags. Has optional LibreTranslate integration (`TRANSLATE = True`; requires a running LibreTranslate instance at the configured URL). Must be rerun when product data changes, then `update.bat` to deploy.
- Google Analytics fires on every page load
- `hof/` = Hall of Fame (featured/top-rated products section)
- Images are `.webp` for performance (check browser support if adding new ones)
- **Product catalog** (2026-04-21): Bulk update to all `static/p/*.html` product pages. New wireless product lines added: Ajazz AK680 Max Wireless (black/yellow), Attack Shark R85 (black/white).
- **Safari iOS bug**: `position:fixed` inside a `backdrop-filter` parent gets wrong containing block — cart button must be a direct `<body>` child, NOT inside `<header>`
- **Cart button**: `position:fixed; top:auto; bottom:74px; right:20px` on mobile (circle). Base style is `position:fixed; top:12px; right:1.5rem` (desktop overlay). Do NOT set both `top` and `bottom` on a fixed element — it stretches vertically
- **Theme toggle (mobile)**: `.m-theme-toggle` is `position:absolute; top:12px; left:12px` inside `.hero` — visible only while hero is in viewport, scrolls away with it
- **Image optimizer**: `scripts/optimize_images.py --convert` converts jpg/png to webp. Run `--apply` to delete originals. Auto-runs via `generate_products.py`. Requires `pip install Pillow`
- **SEO canonical domain**: Everything (canonical, sitemap, OG, JSON-LD, `SITE_URL` at `generate_products.py:59`) must reference `https://m99gadgets.app`. Never `.com` — user does not own the `.com`. If it drifts back, Google will deindex the site.
- **DNS sanity check**: `nslookup -type=ns m99gadgets.app 1.1.1.1` should return `*.nsone.net` (Netlify). If it returns `*.name.com`, the NS swap at name.com was reverted and the domain is dark.

---

## Backup Log
See [[../chat-history/m99gadgets-chats|Chat History]] · [[../backups/m99gadgets-backup|Backup History]]
