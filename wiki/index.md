# Code Vault

> Knowledge base for `~/OneDrive - Technical University of Moldova/Code/`
> Open `graphify-out/` as an Obsidian vault.
> Last graph build: 2026-04-19 · 379 files · 344 nodes · 462 edges · 51 communities

---

## Projects

| Project | Stack | What it is |
|---------|-------|-----------|
| [[projects/999-AutoPost\|999 AutoPost]] | Python + Playwright | Desktop GUI — auto-reposts listings on 999.md |
| [[projects/999-CarScrapper\|999 CarScrapper]] | Python async + FastAPI + SQLite + vanilla JS | Async scraper for 999.md cars (88k) + web UI with photo gallery, price-history sparklines, dashboard |
| [[projects/ASP-Scrapper\|ASP Scrapper]] | Python + Playwright | Desktop GUI — checks DECA exam availability |
| [[projects/Site\|Site]] | HTML/JS/CSS | Frontend marketplace website (buy/sell) |
| [[projects/m99gadgets\|m99gadgets]] | Node.js + Python | Gadget e-commerce product listing site |
| [[projects/Python\|Python]] | Python | Scripts, ML experiments, bots, university labs |
| [[projects/LowBitrate-Blur\|LowBitrate Blur]] | Python + Pillow/numpy/scipy | CLI that degrades AI photos to look like real phone-camera shots (painted low-light look) |
| [[projects/AI-Girl-Catalog\|AI Girl Catalog]] | AI image gen | Reference library — model refs, scene backgrounds (door variants), wardrobe/cosplays |
| [[projects/AI-Girl-Pipeline\|AI Girl Pipeline]] | ComfyUI + Z-Image Turbo + ReActor | Local gen pipeline (Moody/ZIT) + face-swap + character-LoRA dataset effort |
| [[ai-girl-lora-training-local\|AI Girl — Local LoRA Training Runbook]] | ai-toolkit + Z-Image | Recipe that trained `a1g1rl` LoRA locally on 8 GB (py3.12, float8+offload, 2500 steps) |
| [[projects/AI-Cosplay-Model-Room\|AI Cosplay Model Room]] | AI image gen | Art-direction + cross-scene consistency notes for an AI cosplay-girl's bedroom set |
| [[projects/C-Labs\|C Labs]] | C | University C programming labs (PC, SDA, NA) |
| [[projects/Java-OOP\|Java OOP]] | Java | Phone charging simulation — OOP coursework |
| [[projects/POO-Labs\|POO Labs]] | Java | OOP lab series (LAB2–LAB6) |
| [[projects/AA-Labs\|AA Labs]] | ? | Algorithm Analysis university labs |
| [[projects/Tournament\|Tournament]] | Python | Competition bot (team_07) |
| [[projects/Roblox\|Roblox]] | Luau | Forest-themed Roblox game scripts |
| [[projects/car-traffic-simulation\|Car Traffic Simulation]] | Python + SUMO | Microscopic Chișinău traffic sim — OSM → netconvert → TraCI |
| [[projects/PaleGarden\|PaleGarden]] | Godot 4.3 + GDScript | 2D pixel-horror garden sim — first game, 10-agent gamedev team, 4 endings (DAG) |

---

## Knowledge

| File | What's in it |
|------|-------------|
| [[ui-templates\|UI Templates]] | Copy-paste CSS + CTk snippets from all your projects |
| [[skills-installed\|Skills Installed]] | All Claude Code skills, tools, plugins — current + planned |
| [[preferences\|Preferences]] | My coding style, tools, AI rules |
| [[mistakes\|Mistakes]] | Past mistakes & lessons learned — read at session start |
| [[file-history\|File History]] | Auto-backed up old code before edits (via PreToolUse hook) |
| [[decisions\|Global Decisions]] | Cross-project patterns & rules (CSS bugs, Python idioms, etc.) |
| [[999-CarScrapper-ratelimit-throttle-dns\|999 Scraper Rate-limit/Throttle/DNS Runbook]] | Diagnosing 999.md bans vs soft-throttle vs `getaddrinfo`; concurrency budget; backlog drain |
| [[999-CarScrapper-dedup-consistency\|999 Scraper Dedup Consistency]] | Unique cars vs raw listings; every dedup variant (grid / model_stats / sell-through / facets / year-breakdown) + the golden rule for keeping counts in sync |
| [[999-CarScrapper-relist-phash-tuning\|999 Scraper Relist pHash Tuning]] | Why dealer relists slipped past the matcher (CDN re-encode drift + narrow scan window); threshold 6→10 / first-N 3→8 tuning + FP validation; `merge_relists.py` non-destructive re-cluster tool |
| [[999-CarScrapper-relist-identity-rethink\|999 Scraper Relist Identity Rethink]] | The opposite problem: the matcher's FALSE merges. pHash collides for different cars in the same dealer showroom (proven); SM6 is a real cross-post; the rarity law; new gate + two-tier + clique + ORB design. **→ SHIPPED, see next row.** |
| [[999-CarScrapper-relist-v2-deploy\|999 Scraper Relist v2 — Shipped + Deploy]] | The shipped tier-A/S/B + clique model: chimeras 540→0; 3 precision fixes (self-defeating rarity, placeholder poisoning, generic-fingerprint); batch deploy (`apply_clusters`) + continuous `recluster_loop` + `lookup`; the deploy runbook. |
| [[999-CarScrapper-web-perf-indexes\|999 Scraper Web UI Performance]] | Why the page loaded slow (grid 600 ms, listing 800 ms, facets/stats ~10 s) + the fixes: paginate-first query rewrite, missing history indexes, `offer_type`-covering facet indexes, grid-loads-first front-end reorder. Golden list of web-UI indexes. |
| [[new-device-setup\|New Device Setup]] | Step-by-step: bring a fresh machine to the same Claude+vault state |
| [[GRAPH_REPORT\|Graph Report]] | Auto-generated: communities, god nodes, connections |

---

## Decisions (per project)

| Project | Decisions |
|---------|-----------|
| 999 AutoPost | [[decisions/999-AutoPost-decisions\|decisions]] |
| 999 CarScrapper | [[decisions/999-CarScrapper-decisions\|decisions]] |
| ASP Scrapper | [[decisions/ASP-Scrapper-decisions\|decisions]] |
| Site | [[decisions/Site-decisions\|decisions]] |
| m99gadgets | [[decisions/m99gadgets-decisions\|decisions]] |
| Python | [[decisions/Python-decisions\|decisions]] |
| C Labs | [[decisions/C-Labs-decisions\|decisions]] |
| Java | [[decisions/Java-OOP-decisions\|decisions]] |
| POO Labs | [[decisions/POO-Labs-decisions\|decisions]] |
| AA Labs | [[decisions/AA-Labs-decisions\|decisions]] |
| Tournament | [[decisions/Tournament-decisions\|decisions]] |
| Roblox | [[decisions/Roblox-decisions\|decisions]] |
| Car Traffic Simulation | [[decisions/car-traffic-simulation-decisions\|decisions]] |
| PaleGarden | [[decisions/PaleGarden-decisions\|decisions]] |
| AI Girl | [[decisions/AI-Girl-decisions\|decisions]] |

---

## Todo (per project)

| Project | Todo |
|---------|------|
| 999 AutoPost | [[todo/999-AutoPost-todo\|todo]] |
| 999 CarScrapper | [[todo/999-CarScrapper-todo\|todo]] |
| ASP Scrapper | [[todo/ASP-Scrapper-todo\|todo]] |
| Site | [[todo/Site-todo\|todo]] |
| m99gadgets | [[todo/m99gadgets-todo\|todo]] |
| Python | [[todo/Python-todo\|todo]] |
| C Labs | [[todo/C-Labs-todo\|todo]] |
| Java | [[todo/Java-OOP-todo\|todo]] |
| POO Labs | [[todo/POO-Labs-todo\|todo]] |
| AA Labs | [[todo/AA-Labs-todo\|todo]] |
| Tournament | [[todo/Tournament-todo\|todo]] |
| Roblox | [[todo/Roblox-todo\|todo]] |
| Car Traffic Simulation | [[todo/car-traffic-simulation-todo\|todo]] |
| PaleGarden | [[todo/PaleGarden-todo\|todo]] |
| AI Girl | [[todo/AI-Girl-todo\|todo]] |

---

## Chat History (per project)

| Project | Chat Log |
|---------|---------|
| 999 AutoPost | [[chat-history/999-AutoPost-chats\|chats]] |
| 999 CarScrapper | [[chat-history/999-CarScrapper-chats\|chats]] |
| ASP Scrapper | [[chat-history/ASP-Scrapper-chats\|chats]] |
| Site | [[chat-history/Site-chats\|chats]] |
| m99gadgets | [[chat-history/m99gadgets-chats\|chats]] |
| Python | [[chat-history/Python-chats\|chats]] |
| C Labs | [[chat-history/C-Labs-chats\|chats]] |
| Java | [[chat-history/Java-chats\|chats]] |
| POO Labs | [[chat-history/POO-Labs-chats\|chats]] |
| AA Labs | [[chat-history/AA-Labs-chats\|chats]] |
| Tournament | [[chat-history/Tournament-chats\|chats]] |
| Roblox | [[chat-history/Roblox-chats\|chats]] |
| Car Traffic Simulation | [[chat-history/car-traffic-simulation-chats\|chats]] |
| PaleGarden | [[chat-history/PaleGarden-chats\|chats]] |
| AI Girl | [[chat-history/AI-Girl-chats\|chats]] |

---

## Backups (per project)

| Project | Backup Log |
|---------|-----------|
| 999 AutoPost | [[backups/999-AutoPost-backup\|backup]] |
| ASP Scrapper | [[backups/ASP-Scrapper-backup\|backup]] |
| Site | [[backups/Site-backup\|backup]] |
| m99gadgets | [[backups/m99gadgets-backup\|backup]] |
| Python | [[backups/Python-backup\|backup]] |
| C Labs | [[backups/C-Labs-backup\|backup]] |
| Java | [[backups/Java-backup\|backup]] |
| POO Labs | [[backups/POO-Labs-backup\|backup]] |
| AA Labs | [[backups/AA-Labs-backup\|backup]] |
| Tournament | [[backups/Tournament-backup\|backup]] |
| Roblox | [[backups/Roblox-backup\|backup]] |

---

## How to Use

**Ask Claude about the code:**
```
graphify query "how does the 999 AutoPost scraper work"
graphify query "what files are in the Site project"
```

**After you edit files yourself (outside Claude):**
```bash
cd "C:/Users/SURFACE/OneDrive - Technical University of Moldova/Code"
graphify update .
```

**Obsidian tips:**
- `Ctrl+O` — quick open any note
- `Ctrl+G` — open graph view
- Click any `[[link]]` to navigate
