# 999 AutoPost

> Auto-repost listings on 999.md · Desktop GUI · Multi-account · Dark theme
> **Last synced**: 2026-06-05 21:42

**Path**: `Code/999 AutoPost/`
**Stack**: JSON, Python, Markdown
**Platform**: Windows `.exe`

---

## What It Does

### User Experience
- Opens a dark-themed desktop window
- Switch between multiple 999.md accounts from a sidebar
- See all active listings as cards: thumbnail (80×60px) + title + price + ID
- Check boxes next to listings → click "Repost Selected" → they get bumped to top automatically
- Toggle a live console panel at the bottom to watch the scraper work in real time
- Cached listings per account — re-opening is instant; refresh only when needed
- Add/remove accounts via a modal dialog

### System Experience
- `app.py` — CustomTkinter GUI, all widget layout, threading for async tasks
- `main.py` (imported as `core`) — Playwright browser automation, scraping logic
- `build.py` / `999AutoPost.spec` — PyInstaller bundler
- Data stored in `data/<username>/` (listings cache, repost log, blacklist, images)
- Credentials in `data/accounts.json` (never committed)

---

## Key Files
| File | Role |
|------|------|
| `app.py` | GUI entry point |
| `main.py` | Scraper/automation core |
| `build.py` | Build to .exe |
| `999AutoPost.spec` | PyInstaller config |
| `data/` | Per-account cache (listings, images, logs, blacklist) |
| `assets/logo.png` | App logo |
| `requirements.txt` | Python dependencies |
| `README.md` | Setup & feature docs (multi-account, repost, scraping) |

---

## Design System (CustomTkinter)

### Color Palette
```python
_ACCENT       = "#e53935"   # vibrant red — buttons, checkboxes, CTA
_ACCENT_HOVER = "#c62828"   # red hover state
_ACCENT_DARK  = "#b71c1c"   # deep red (pressed/active)
_BG_DARK      = "#121212"   # main window background
_CARD_DARK    = "#1e1e1e"   # listing card + dialog bg
_CARD_HOVER   = "#262626"   # card hover state
_SIDEBAR_BG   = "#181818"   # left sidebar
_SUBTLE_TEXT  = "#9e9e9e"   # secondary labels, meta info
_DIVIDER      = "#2a2a2a"   # borders, dividers, separators
```

### Theme
```python
ctk.set_appearance_mode("dark")      # dark mode always on
ctk.set_default_color_theme("blue")  # base theme (overridden by _ACCENT red)
```

### Typography
```python
ctk.CTkFont(size=16, weight="bold")   # section headers
ctk.CTkFont(size=13, weight="bold")   # card titles
ctk.CTkFont(size=11)                  # labels
ctk.CTkFont(size=20)                  # placeholder icons
```

### Component Snippets

**Listing Card Row**
```python
class ListingRow(ctk.CTkFrame):
    # fg_color = (_CARD_DARK, _CARD_DARK)
    # border_width=1, border_color=(_DIVIDER, _DIVIDER)
    # Contains: CTkCheckBox (red), thumbnail (80×60), title label, price label
```

**Thumbnail**
```python
ctk.CTkFrame(parent, width=80, height=60,
             fg_color=("#2a2a2a", "#2a2a2a"), corner_radius=8)
# Image loaded via CTkImage(PIL.Image, size=(76, 56))
```

**Primary Button (Red)**
```python
ctk.CTkButton(self, text="Save Account", width=308, height=38,
              fg_color=_ACCENT, hover_color=_ACCENT_HOVER,
              font=ctk.CTkFont(size=13, weight="bold"))
```

**Entry Field**
```python
ctk.CTkEntry(self, width=308, height=36, border_color=_DIVIDER)
```

---

## Layout Wireframe
```
┌─────────────────────────────────────────────────────────────┐
│  999 AutoPost                                    [─][□][×]  │
├──────────────┬──────────────────────────────────────────────┤
│              │  Account: john@example.com  [↻ Refresh]      │
│  SIDEBAR     ├──────────────────────────────────────────────┤
│  ──────────  │  ☐ [img] Title of listing            120 MDL │
│  john@...    │  ☐ [img] Another listing              85 MDL │
│  ──────────  │  ☐ [img] Third listing                50 MDL │
│  + Add Acct  │  ☐ [img] ...                                 │
│              │                                              │
│  [bg=#181818]│  [Repost Selected (3)]    [Select All]       │
│              ├──────────────────────────────────────────────┤
│              │  ▼ Console                                   │
│              │  [2026-04-19] Logging in...                  │
│              │  [2026-04-19] Found 12 listings              │
└──────────────┴──────────────────────────────────────────────┘

Add Account Dialog (modal):
┌──────────────────────────────┐
│  Add 999.md Account          │
│  Username or Email           │
│  [________________________]  │
│  Password                    │
│  [________________________]  │
│  [      Save Account       ] │  ← red button
└──────────────────────────────┘
```

---

## Run & Build
```bash
# Run from source
python app.py

# Build .exe
python build.py
# or: pyinstaller 999AutoPost.spec
```

---

## Data Structure
```
data/
  accounts.json              ← [{username, password}, ...]
  <username>/
    listings.json            ← cached listing data
    repost_log.json          ← history of reposts
    blacklist.json           ← URLs to skip
    images/                  ← cached listing thumbnails
```

---

## Notes & Gotchas
- Playwright needs Chromium: `python -m playwright install chromium`
- PyInstaller frozen: `sys._MEIPASS` used for asset paths (not `__file__`)
- `core.DATA_DIR` overridden in `app.py` before any core call — order matters
- `main.py` is imported as `core` to avoid name clash with Python builtins
- Threading: async Playwright runs in a background thread; UI updated via `after()`

---

## Backup Log
See [[../chat-history/999-AutoPost-chats|Chat History]] · [[../backups/999-AutoPost-backup|Backup History]]
