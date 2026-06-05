# ASP Scrapper — ASP Exam Checker

> DECA exam slot checker · Dark blue desktop GUI · Telegram notifications
> **Last synced**: 2026-06-05 21:42

**Path**: `Code/ASP Scrapper/`
**Stack**: Python, JSON, Markdown, Batch
**Language**: Romanian UI
**Platform**: Windows `.exe`

---

## What It Does

### User Experience
- Opens a dark blue desktop window split into two panels
- **Left panel (SETARI — Settings)**: scrollable form with all credentials:
  - IDNP (national ID number)
  - First name + Last name
  - Phone + Email
  - ID series/number + expiry date (day/month/year fields)
  - Medical certificate number
  - Telegram Bot Token + Chat ID (for notifications)
- **Right panel**: results + embedded console showing scrape progress
- Click check → app scrapes DECA website with Playwright
- Shows exam slot availability for Martie & Aprilie 2026
- Sends Telegram notification when a slot is found

### System Experience
- `app.py` — CustomTkinter GUI (dark mode, blue theme), async runner via threading
- `launcher.py` — entry point, handles frozen vs source path resolution
- `scrapper.py` (in `dist/`) — async Playwright logic targeting DECA site
- `credentials.json` — saved form data (gitignored)
- Queue-based console: `app.py` feeds log messages to a `queue.Queue`, GUI drains it

---

## Key Files
| File | Role |
|------|------|
| `app.py` | GUI + async orchestration |
| `launcher.py` | Entry point (path resolution) |
| `ASP Exam Checker.spec` | PyInstaller config |
| `BUILD.bat` | One-click build |
| `credentials.json` | Saved login (gitignored) |
| `asp_logo.ico` / `.png` | App icon |
| `README.md` | Setup guide (Romanian) — install, build, usage |

---

## Design System (CustomTkinter)

### Theme
```python
ctk.set_appearance_mode("dark")       # always dark
ctk.set_default_color_theme("blue")   # blue accent (CTk default blue)
```

### Layout
```python
# Two-column grid layout
settings_frame = ctk.CTkFrame(self)   # left — settings/credentials
results_frame  = ctk.CTkFrame(self)   # right — output + console

settings_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
# Scrollable inner frame for all form fields
scrollable = ctk.CTkScrollableFrame(settings_frame, fg_color="transparent")
```

### Typography
```python
ctk.CTkFont("Arial", 14, "bold")   # section header "SETARI"
ctk.CTkFont("Arial", 10)           # field labels
ctk.CTkFont("Arial", 9)            # small sub-labels (day/month/year)
```

### Form Fields (Romanian labels)
```
IDNP:              [_____________________]
Prenume:  [______]  Nume:  [______]
Telefon:  [______]  Email: [______]
Seria/Nr. buletin: [_____________________]
Data buletin:   Zi:[__] Luna:[__] An:[____]
Certificat medical: [_____________________]

── Telegram ──
Bot Token: [_____________________________]
Chat ID:   [_____________________________]

[VERIFICA DISPONIBILITATEA]  ← big blue button
```

---

## Layout Wireframe
```
┌─────────────────────────────────────────────────────────────┐
│  ASP Exam Checker                                [─][□][×]  │
├──────────────────────────┬──────────────────────────────────┤
│  SETARI                  │  REZULTATE                       │
│  ──────────────────────  │  ────────────────────────────    │
│  IDNP:                   │                                  │
│  [___________________]   │  Status: ⏳ Se verifica...       │
│                          │                                  │
│  Prenume:   Nume:        │  ┌──────────────────────────┐   │
│  [________] [________]   │  │ Console log              │   │
│                          │  │ > Connecting to DECA...  │   │
│  Telefon:   Email:       │  │ > Checking March slots.. │   │
│  [________] [________]   │  │ > No slots available     │   │
│                          │  └──────────────────────────┘   │
│  Seria buletin:          │                                  │
│  [___________________]   │                                  │
│  Zi:[__] Luna:[__] An:[] │                                  │
│                          │                                  │
│  Certificat medical:     │                                  │
│  [___________________]   │                                  │
│  ── Telegram ──          │                                  │
│  Token: [_____________]  │                                  │
│  Chat ID: [___________]  │                                  │
│                          │                                  │
│  [VERIFICA]              │                                  │
└──────────────────────────┴──────────────────────────────────┘
```

---

## Run & Build
```bash
# Run from source
python launcher.py

# Build .exe (one click)
BUILD.bat
# Output: dist/ASP Exam Checker.exe
```

---

## Auto-Update Appointment (added 2026-05-28)

When the scrapper detects an available day **strictly earlier** than the user's current appointment at the configured target DECA location, it automatically rebooks via `https://eservicii.gov.md/asp/dimtcca/APO/my-appointments`:

```
my-appointments → fill IDNP + Codul programării + Numărul cererii → CĂUTARE
  ├ error "Verificați corectitudinea" → TG alert, reload, retry up to 3×
  └ success → MODIFICĂ → DA → open date picker
              ├ calendar empty → reload up to 10× (TG alert if all fail)
              └ pick target date → earliest Ora → PROGRAMEAZĂ-TE → confirm
```

Runs in a **new tab in the existing browser context**, so the main check loop is unaffected. After success, the in-memory `current_appointment_date` is updated so the same slot doesn't re-trigger; monitor keeps running.

Config (in `credentials.json`, GUI labels in parens):
- `auto_update_enabled` (toggle "Activeaza auto-update programare")
- `appointment_code` ("Codul programarii", APO…)
- `request_number` ("Numarul cererii")
- `target_location` (`CTkOptionMenu` — fixed list of the two DECA Chișinău offices, see `TARGET_LOCATIONS` in `app.py`)
- `current_appointment_date` ("Data programare curenta" — 3 entries Zi/Luna/An, composed to `dd.mm.yyyy`)

Key functions in `dist/scrapper.py`: `auto_update_appointment()`, `find_earliest_available()`, `parse_current_appointment_date()`.

See [[../decisions/ASP-Scrapper-decisions|decisions]] for trade-offs (why strict-earlier, why fixed dropdown, why user-typed date).

---

## Notes & Gotchas
- `scrapper.py` must stay in `C:\Users\johns\OneDrive\Code\ASP Scrapper\` — hardcoded path in dist build. **Will break on other machines** unless path is updated
- `aiohttp` and `playwright` imported in `app.py` even when unused — required so PyInstaller bundles them for `scrapper.py`
- Async scraping runs in a background thread; results sent back via `queue.Queue` to avoid GUI freezes
- Telegram notification fires when a slot is detected — requires valid bot token + chat ID
- `credentials.json` must be gitignored — contains personal IDNP + medical cert data

---

## Backup Log
See [[../chat-history/ASP-Scrapper-chats|Chat History]] · [[../backups/ASP-Scrapper-backup|Backup History]]
