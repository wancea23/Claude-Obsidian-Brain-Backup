# UI Templates & Style Reference

> Reusable patterns extracted from your actual projects.
> Copy-paste starting points for new work.

---

## Web Projects

### ClickBox Theme (Site/)
Yellow + Blue marketplace · Light/dark · Segoe UI

```css
/* ── Palette ── */
--yellow:     #ffe600;
--blue:       #0064d2;
--blue-hover: #004a9f;
--bg:         #f3f6fa;
--card:       #ffffff;
--text:       #222222;
--border:     #f0f0f0;
/* Dark mode */
--dark-bg:    #181a1b;
--dark-card:  #23272a;
--dark-text:  #e6e6e6;

/* ── Header ── */
header {
  background: linear-gradient(90deg, #ffe600 80%, #fffbe6 100%);
  padding: 1rem 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  display: flex; align-items: center; justify-content: space-between;
}

/* ── Card ── */
.card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  border: 1px solid #f0f0f0;
  overflow: hidden;
  transition: box-shadow 0.22s, transform 0.18s;
}
.card:hover {
  box-shadow: 0 8px 32px rgba(0,100,210,0.10);
  transform: translateY(-4px) scale(1.025);
  border-color: #ffe600;
}

/* ── Grid ── */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.5rem; padding: 2rem;
}

/* ── Button ── */
.btn {
  background: #0064d2; color: #fff; border: none;
  padding: 0.7rem 1.5rem; border-radius: 6px; font-weight: 500;
  cursor: pointer; transition: background 0.18s, transform 0.15s;
}
.btn:hover { background: #004a9f; transform: translateY(-2px) scale(1.04); }

/* ── Logo SVG ── */
/* Gradient blue checkmark in rounded square — see Site/index.html */
```

---

### M99 Gadgets Theme (m99gadgets/)
Orange + Dark · Glassmorphism header · Flip cards · Space Grotesk

```css
/* ── Palette (CSS vars) ── */
:root {
  --bg:      #f2f1ed;    --surface: #ffffff;
  --ink:     #0f1117;    --ink2:    #374151;   --muted: #6b7280;
  --accent:  #fe5000;    --accent-hover: #e8490a;
  --green:   #059669;    --gl: #dcf5ec;
  --amber:   #d97706;    --al: #fef0c7;
  --red:     #dc2626;    --rl: #fce8e8;
  --shadow-sm: 0 1px 2px rgba(17,24,39,.04), 0 4px 16px rgba(17,24,39,.06);
  --shadow-glow: 0 4px 16px rgba(254,80,0,0.35);
}
/* Dark: add class="dark" on <html> */

/* ── Fonts ── */
/* @import Space Grotesk (body), Bebas Neue (display), JetBrains Mono (code) */
body { font-family: 'Space Grotesk', sans-serif; }
h1, .display { font-family: 'Bebas Neue', sans-serif; letter-spacing: .04em; }
.mono { font-family: 'JetBrains Mono', monospace; }

/* ── Motion ── */
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);  /* bouncy */
--ease-out:    cubic-bezier(0.16, 1, 0.3, 1);

/* ── Glass Header ── */
header {
  background: rgba(255,255,255,0.82);
  backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid rgba(17,24,39,0.07);
  position: sticky; top: 0;
}

/* ── Dark Hero ── */
.hero {
  background:
    radial-gradient(ellipse 140% 80% at 50% 110%,
      rgba(254,80,0,0.22) 0%, transparent 65%),
    linear-gradient(180deg, #17171c 0%, #0c0c10 100%);
  color: #f9fafb;
}

/* ── Flip Card ── */
.card-front, .card-back {
  backface-visibility: hidden;
  transition: transform 0.5s cubic-bezier(0.175,0.885,0.32,1.275);
}
.card-back { transform: perspective(1200px) rotateY(-180deg); }
/* On click: toggle .flipped → front rotates 180deg away, back rotates in */

/* ── Pulsing Badge ── */
@keyframes pulseGlow {
  0%  { box-shadow: 0 0 0 0 rgba(254,80,0,.4); }
  70% { box-shadow: 0 0 0 6px rgba(254,80,0,0); }
}
.badge { animation: pulseGlow 2s infinite; }
```

---

## Desktop Apps (Python / CustomTkinter)

### 999 AutoPost Theme
Dark red accent · Material dark

```python
# Color constants
_ACCENT       = "#e53935"   # red
_ACCENT_HOVER = "#c62828"
_BG_DARK      = "#121212"   # window bg
_CARD_DARK    = "#1e1e1e"   # card / panel
_CARD_HOVER   = "#262626"
_SIDEBAR_BG   = "#181818"
_SUBTLE_TEXT  = "#9e9e9e"   # secondary text
_DIVIDER      = "#2a2a2a"   # border

ctk.set_appearance_mode("dark")

# Reusable button
ctk.CTkButton(parent,
  fg_color=_ACCENT, hover_color=_ACCENT_HOVER,
  font=ctk.CTkFont(size=13, weight="bold"),
  height=38, corner_radius=6)

# Reusable card frame
ctk.CTkFrame(parent,
  fg_color=(_CARD_DARK, _CARD_DARK),
  border_width=1, border_color=(_DIVIDER, _DIVIDER),
  corner_radius=8)

# Thumbnail frame
ctk.CTkFrame(parent, width=80, height=60,
  fg_color=("#2a2a2a","#2a2a2a"), corner_radius=8)
```

---

### ASP Scrapper Theme
Dark blue · Standard CTk blue · Two-panel layout

```python
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Two-panel layout pattern
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=2)

left  = ctk.CTkFrame(app)
right = ctk.CTkFrame(app)
left.grid( row=0, column=0, padx=10, pady=10, sticky="nsew")
right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

# Scrollable form panel
scrollable = ctk.CTkScrollableFrame(left, fg_color="transparent")
scrollable.pack(fill="both", expand=True)

# Console output (read-only textbox)
console = ctk.CTkTextbox(right, state="disabled")
# To append: console.configure(state="normal"); console.insert("end", msg); console.configure(state="disabled")

# Queue-based thread-safe console update
import queue
log_queue = queue.Queue()
def poll_queue():
    while not log_queue.empty():
        msg = log_queue.get_nowait()
        console.configure(state="normal")
        console.insert("end", msg + "\n")
        console.configure(state="disabled")
    app.after(100, poll_queue)
```

---

## Common Patterns

### PyInstaller Asset Path (both apps use this)
```python
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    BASE = Path(sys._MEIPASS)   # inside .exe bundle
else:
    BASE = Path(__file__).parent  # running from source

ASSETS = BASE / "assets"
```

### Async in CTk (threading pattern)
```python
import asyncio, threading

def run_async(coro):
    def _run():
        asyncio.run(coro)
    threading.Thread(target=_run, daemon=True).start()

# Usage
run_async(my_playwright_scraper())
```

### Playwright Browser Viewport
```python
ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
```

---

## Related
- [[projects/Site|Site project]]
- [[projects/m99gadgets|m99gadgets project]]
- [[projects/999-AutoPost|999 AutoPost project]]
- [[projects/ASP-Scrapper|ASP Scrapper project]]
