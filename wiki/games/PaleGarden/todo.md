# The Pale Garden — Todo (human-readable mirror of tasks.md)

> Owned by Director. Mirrors `Code/Games/PaleGarden/tasks.md` with [[wikilinks]] for navigation.

## Phase 0 — Bootstrap

- [x] Godot 4.6 project scaffolded (project.godot updated to 4.6 by editor on first open)
- [x] All autoloads: Constants, GameState, DayManager, AudioManager, DialogueManager
- [x] content/*.json: journal entries, NPC dialogue, events, whispers scaffold
- [x] Placeholder SVG sprites for all 10 needed art assets
- [ ] **game-designer** writes GDD.md + [[narrative/storyline-graph]] DAG
- [ ] **reviewer** smoke test + STYLE.md audit

## Phase 1 — Act 1 (Days 1–14) ✓

- [x] [[mechanics/garden-grid]] — Garden.tscn, 8×6 TileMap, tool system
- [x] [[mechanics/plant-state-machine]] — Crop.tscn, day-driven phases, weed flag
- [x] Farm.tscn + farm.gd — all 14 day events, tutorial, rest/journal loop
- [x] Market.tscn + market.gd — Day 7 + Day 14 with NPCs
- [x] NPCs: Margaret (fence sidequest), Bruno (naming + flag), TheSeller (JS-01)
- [x] Minigames: PlantingMinigame, MarketBartering, FenceRepair, ScarecrowAssembly
- [x] UI: HUD, Journal, DayTransition, DialogueBox (choice mode), NamingPopup
- [ ] **artist** — real sprites from asset_requests.json (currently SVG placeholders)
- [ ] **audio-engineer** — 8 tracks from audio_requests.json (game runs without them)
- [ ] **tester** — smoke test + Day 1→7→14 playthrough

## Phase 2 — Act 2 (Days 15–25)

- [ ] Plant entity (TheEntity.tscn) with whisper floating text system
- [ ] Day 20 tendril environmental horror (3am window scene)
- [ ] Day 22 Scarecrow turns — JS-02
- [ ] Day 25 first demand — bloodletting rhythm minigame (MG-3)
- [ ] HUNGER/CONSCIENCE display in HUD from Day 5
- [ ] Act 2 audio: wrong note in piano motif, breathing under ambient

## Phase 3+ — Acts 3–5

To be planned after Act 2 sign-off.
