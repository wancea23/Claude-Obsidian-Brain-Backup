---
project: The Pale Garden
type: todo
last_updated: 2026-05-05
---

# Todo

Mirrors `tasks.md` in the project but with vault-side context.

## Done — 2026-04-30
- [x] Walkable farm map (640×640) with painted ground
- [x] Player character with WASD, walk-bob, facing direction
- [x] Three interaction zones (garden / house / market) with [E] prompt
- [x] Garden modal menu (TILL / WATER / PLANT / HARVEST cards)
- [x] Stamina system (6 dots, restored on sleep)
- [x] Time-of-day visual cycle (morning → noon → evening → night)
- [x] Crop variety (turnip / tomato / pumpkin) with type-coloured visuals + per-type prices
- [x] Tutorial dialogue trigger on Day 1
- [x] Inventory display in HUD
- [x] Trees, flowers, well, mailbox, scarecrow, fences, farmhouse details
- [x] Camera follows player with map-edge limits
- [x] House StaticBody2D collision

## Next — Highest impact
- [ ] **Sleep cutscene** — black fade + "Day N" title + fade-in (replaces current journal-modal-only flow)
- [ ] **Tomato/pumpkin seed unlock at market** — wire into Day 7 trade offers (`content/npc_dialogue.json` `trade_offers.day_7`)
- [ ] **NPC `[E] Talk` prompt** — proximity check; currently NPCs respond only to mouse click via Area2D
- [ ] **Bundle minimal SFX** so `AudioManager.play_sfx("water_splash")` etc. actually plays — even short generic clips

## Polish
- [ ] **Footstep dust** — 2×2 tan rect spawned at Elias's feet every 0.4s while walking, fades over 0.5s
- [ ] **Harvest sparkle** — small expanding ring of yellow particles when ripe crop is picked
- [ ] **Water splash** — 3-frame blue particle burst on watered tile
- [ ] **Tile hover refinement** — use crop type color when hovering an empty tile in PLANT mode

## Acts 2+ groundwork (not Act 1)
- [ ] Plant entity (TheEntity.tscn) — the blood plant introduced Day 15
- [ ] Whisper system — floating pixel text above plant in plant's leaf color
- [ ] Day 17 first whisper: "warm."
- [ ] Bloodletting minigame (rhythm, heartbeat-based)

## Done — 2026-05-05
- [x] Elias walk animations — LPC v1 sheet, rows 8–11, 9 frames, N/W/S/E
- [x] Elias directional idle — LPC v1 sheet, rows 22–25, 2 frames, facing last-walked direction
- [x] Removed legacy `elias_sheet.png` dependency — everything from `elias_v1.png`
- [x] `_facing` variable in `elias.gd` for correct idle direction on stop
- [x] LPC row order convention saved to memory (N,W,S,E applies to all characters)

## Next — Sprites
- [ ] **NPC sprites** — source or generate LPC sheets for Margaret, Bruno, The Seller (same convention: LPC generator, rows 8–11 walk, 22–25 idle)
- [ ] **World sprites** — farmhouse, trees, crops from itch.io / OpenGameArt / user's own assets
- [ ] **Story continuation** — pick up from where Act 1 left off (see narrative.md)

## Tech debt / cleanups
- [ ] Convert `farm_ground.gd._draw()` to TileMap when sprite assets land
- [ ] `_npc_layer` is declared but unused after removing ambient Margaret — keep for event-driven spawns

## Story content gaps
- [ ] Verify `content/npc_dialogue.json` has all dialogue keys referenced in code
- [ ] Day 6 `journal_surface` event needs the journal item visual (Area2D sparkle in field)
- [ ] Day 9 `scarecrow_rot` needs visual scarecrow change (cracked/falling)
- [ ] Day 14 `seller_encounter` flow — Seller appears, JS-01 jumpscare wired but Seller scene needs proper market positioning
