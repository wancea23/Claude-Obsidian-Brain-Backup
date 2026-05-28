# Projects Catalog

> All projects in `~/OneDrive - Technical University of Moldova/Code/`

---

## 999 AutoPost
- **Path**: `999 AutoPost/`
- **Stack**: Python, tkinter/GUI, PyInstaller
- **UX**: Desktop app that auto-posts content; has a `.spec` build file → packaged as `.exe`
- **System**: Standalone Python app, no server needed
- **Files**: `app.py`, `assets/`, `build/`
- **Notes**: Has `__pycache__` → actively run locally

---

## 999 CarScrapper
- **Path**: `999 CarScrapper/`
- **Stack**: Python (httpx async, BeautifulSoup, Pillow, FastAPI, uvicorn), SQLite, vanilla JS/HTML/CSS
- **UX**: Background scraper + local web UI (`http://localhost:8000`) to browse/filter/sort 88k car listings from 999.md with photo galleries, price-history sparklines, dashboard
- **System**: GraphQL discovery → BeautifulSoup detail parsing → SQLite (WAL) + WebP photos on `E:\DB\` → FastAPI read-only API + vanilla-JS SPA
- **Files**: `pipeline.py`, `scheduler.py`, `scraper/{crawler,parser,photo,session}.py`, `db/{schema.sql,database.py}`, `web/{app,queries}.py`, `web/static/{index.html,app.js,style.css}`, `config.py`
- **Notes**: Data lives on E: not OneDrive; web app opens DB read-only so it's safe alongside an active scrape; per-host semaphores keep CDN fast and site polite (8.5 min → 70 s for a 2-page test after tuning)

---

## AA Labs (Algorithm Analysis)
- **Path**: `AA Labs/`
- **Stack**: Unknown (Lab1, Lab2 structure)
- **UX**: University lab assignments
- **System**: Academic exercise code

---

## ASP Scrapper
- **Path**: `ASP Scrapper/`
- **Stack**: Python, PyInstaller
- **UX**: Desktop GUI tool that checks ASP exam results; has custom icon (`asp_logo.ico`)
- **System**: Packaged as `.exe`, scrapes web content
- **Files**: `app.py`, `ASP Exam Checker.spec`

---

## C (University C Labs)
- **Path**: `C/`
- **Stack**: C language
- **Sub-folders**:
  - `PC/` — Programming Concepts labs
  - `PC_Teams/` — Team-based PC labs
  - `SDA/` — Data Structures & Algorithms
  - `NA/` — Numerical Analysis
- **UX**: Academic lab submissions
- **System**: Compiled C programs

---

## Java
- **Path**: `Java/`
- **Stack**: Java
- **Files**: `main.java`, `Charger.class`, `Outlet.class`, `images/`
- **Notes**: OOP project — likely an electrical outlet/charger simulation

---

## Python Scripts
- **Path**: `Python/`
- **Stack**: Python
- **Files**: `banana.py`, `banana2.py`, `bitca.py`, `bitcabot/`, `Discrete_L2_5.py`
- **Notes**: Mix of personal scripts and a bot (`bitcabot`)

---

## m99gadgets
- **Path**: `m99gadgets/`
- **Stack**: Node.js, JavaScript
- **UX**: E-commerce/product listing site with generated products
- **System**: Has `package.json`, `data/`, `scripts/`, `hall of fame/`
- **Files**: `generate_products.py`, web scripts

---

## Roblox
- **Path**: `Roblox/`
- **Stack**: Luau (Roblox scripting language)
- **Files**: `ForestClient.luau`, `Script.luau`
- **UX**: Roblox game client/server scripts

---

## Site (Web Marketplace)
- **Path**: `Site/`
- **Stack**: HTML, JavaScript, CSS
- **UX**: Multi-page web marketplace with cart, admin panel, listings
- **System**: Pure frontend, no backend detected
- **Key Files**: `add-listing.html`, `admin.html`, `cart.html`

---

## POO Labs (OOP Labs)
- **Path**: `POO Labs/`
- **Stack**: Java (OOP)
- **Sub-folders**: `POO-LAB2` through `POO-LAB6`
- **UX**: University OOP lab assignments
- **System**: Java class hierarchy exercises

---

## Car Traffic Simulation
- **Path**: `car-traffic-simulation/urban-traffic-sim/`
- **Stack**: Python, SUMO, TraCI, sumolib, PyYAML, matplotlib
- **UX**: Headless + SUMO-GUI microscopic traffic sim of Chișinău; NETEDIT for road editing
- **System**: OSM → netconvert → TraCI orchestration; never-despawn persistence controller
- **Files**: `main.py`, `src/simulation/runner.py`, `src/simulation/persistence.py`, `src/agents/spawner.py`

---

## Tournament
- **Path**: `Tournament/`
- **Stack**: Python
- **Files**: `team_07.py`, `test_bot.py`
- **UX**: Programming competition / bot tournament code
- **Notes**: Has `__pycache__` → actively tested
