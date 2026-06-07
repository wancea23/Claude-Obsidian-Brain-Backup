# Site — ClickBox Marketplace

> Multi-page frontend marketplace · Buy/sell listings with dark mode
> **Last synced**: 2026-06-07 18:48

**Path**: `Code/Site/`
**Stack**: HTML, JavaScript, CSS
**Name**: ClickBox
**Language**: English
**Platform**: Browser only — no backend, localStorage state

---

## What It Does

### User Experience
- Browse item cards in a responsive grid (auto-fit columns)
- Search + filter listings
- Add items to cart (badge counter on nav)
- Watchlist (heart/favorite items)
- User profile page
- Sell your own items via add-listing form
- Admin panel for content management
- Full dark mode toggle (🌙 button)

### System Experience
- Pure HTML + CSS + JS — no framework, no build step
- Each page: `page.html` + `page.js` pair
- `styles.css` — single shared stylesheet (747 lines)
- `script.js` — shared utilities
- State stored in `localStorage`
- Cart badge updates across pages via storage events

---

## Pages
| File | What it is |
|------|-----------|
| `index.html` | Homepage — listing grid + search + hero |
| `item.html` | Single item detail + ratings + offers |
| `add-listing.html` | Create listing form |
| `cart.html` | Cart with qty controls + checkout |
| `watchlist.html` | Saved/favorited items |
| `profile.html` | User profile + seller stats |
| `admin.html` | Admin panel — content moderation |

---

## Design System

### Color Palette
```
Primary Yellow   #ffe600   — header gradient, accents, hover borders
Blue CTA         #0064d2   — buttons, links, focus states
Blue Hover       #004a9f   — button hover state
Body BG          #f3f6fa   — light grey page background
Card BG          #ffffff   — card surface
Text Primary     #222222   — body text
Border           #f0f0f0   — card borders

── Dark Mode ──
Dark BG          #181a1b
Dark Card        #23272a
Dark Text        #e6e6e6
Dark Accent      #ffe600   — same yellow becomes primary text in dark
Dark Button BG   #0050a8
```

### Typography
```
Font Family:  'Segoe UI', Arial, sans-serif
Body:         1rem / #222
H1:           2rem, weight 700, letter-spacing 1px
```

### Spacing & Layout
```
Grid:    auto-fit, minmax(220px, 1fr), gap 1.5rem, padding 2rem
Card:    border-radius 12px, box-shadow 0 2px 12px rgba(0,0,0,0.08)
Card hover: translateY(-4px) scale(1.025), border #ffe600
Button:  padding 0.7rem 1.5rem, border-radius 6px
```

### Component Snippets

**Header**
```css
header {
  background: linear-gradient(90deg, #ffe600 80%, #fffbe6 100%);
  padding: 1rem 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  display: flex; align-items: center; justify-content: space-between;
}
```

**Item Card**
```css
.item-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  border: 1px solid #f0f0f0;
  overflow: hidden;
  cursor: pointer;
  transition: box-shadow 0.22s, transform 0.18s;
}
.item-card:hover {
  box-shadow: 0 8px 32px rgba(0,100,210,0.10);
  transform: translateY(-4px) scale(1.025);
  border-color: #ffe600;
}
.item-card img { width: 100%; height: 160px; object-fit: cover; }
```

**Blue Button**
```css
button {
  background: #0064d2;
  color: #fff;
  border: none;
  padding: 0.7rem 1.5rem;
  border-radius: 6px;
  font-weight: 500;
  transition: background 0.18s, transform 0.15s;
}
button:hover {
  background: #004a9f;
  transform: translateY(-2px) scale(1.04);
}
```

**Seller Badges**
```css
/* Top seller */  .seller-badge.top   { background: linear-gradient(90deg, #ffe600, #ffd700); color: #222; }
/* Trusted */     .seller-badge.trusted { background: #b6fcb6; color: #006400; }
/* New */         .seller-badge.new   { background: #d0d6e0; color: #333; }
```

---

## Layout Wireframe
```
┌─────────────────────────────────────────────────────┐
│ 🟨 CLICKBOX          [Profile] [Watchlist] [Cart] [Sell Now] │
├─────────────────────────────────────────────────────┤
│              Hero / Search Bar                       │
├─────────────────────────────────────────────────────┤
│  [Card] [Card] [Card] [Card]   ← auto-fit grid       │
│  [Card] [Card] [Card] [Card]                         │
│  img(160px) / title / price / badge                  │
├─────────────────────────────────────────────────────┤
│              Pagination / Load More                  │
└─────────────────────────────────────────────────────┘
```

---

## Logo
```html
<!-- SVG logo used in header -->
<svg width="36" height="36" viewBox="0 0 36 36">
  <rect width="36" height="36" rx="8" fill="url(#logo-gradient)"/>
  <path d="M10 18L16 24L26 12" stroke="white" stroke-width="3"
        stroke-linecap="round" stroke-linejoin="round"/>
  <defs>
    <linearGradient id="logo-gradient" x1="0" y1="0" x2="36" y2="36">
      <stop stop-color="#0064d2"/>
      <stop offset="1" stop-color="#00c6ff"/>
    </linearGradient>
  </defs>
</svg>
```

---

## Responsive Breakpoints
```
< 900px  — watchlist grid collapses to minmax(180px,1fr)
< 600px  — single column, full-width cards
< 600px  — controls stack vertically
```

---

## Dark Mode
Toggle via class `body.dark-mode`. Stored in localStorage.
Key dark overrides: bg `#181a1b`, cards `#23272a`, accent text `#ffe600`, headers gradient `#222→#333`.

---

## Notes & Gotchas
- No backend — all data in localStorage (resets on clear)
- `script.js` handles cart sync across tabs via `storage` event
- Cart badge (`#cart-badge`) is updated from every page's JS
- Seller badges: `.top` `.trusted` `.new` — set per-listing in data
- Star rating system in `item.js`
- Admin panel has no auth — purely frontend (localhost use only)

---

## Backup Log
See [[../chat-history/Site-chats|Chat History]] · [[../backups/Site-backup|Backup History]]
