# Phase 2 — Days 1-3 Foundation Experience

**Status:** ⏳ Pending · **Goal:** Tutorial works on Day 1, planting/watering/harvest loop feels tactile, Days 2-3 establish rhythm without prompts.

## Prerequisites
- Phase 1 ✅
- Decision needed: bookshelf strings to JSON before/during this phase? (Phase 1 debt)

## Steps

### Yard redesign — completed 2026-05-28

**Read this first if you're picking up from a new chat.** Mid-session the user switched the main scene from `scenes/Main.tscn` (procedural Farm built by `yard_tool.gd`) to `scenes/world/yard.tscn` (a hand-authored Yard with House, Magazie, BarnBody, BarnRoof, Fence, BarnFence, Garden, Vegetation tilemaps + Elias CharacterBody2D). The old Farm.tscn architecture is dormant; everything below targets the new Yard.

**What's in the Yard right now**:
- `/root/Yard/Elias` (CharacterBody2D, spawn (320, 180), Camera2D auto-attached, 8-direction LPC animations from `assets/sprites/Elias/elias_v1.png`)
- `/root/Yard/Collisions` (Node2D, script `scenes/world/yard_collisions.gd`)
- `/root/Yard/Zones` (Node2D, script `scenes/world/yard_zones.gd`)
- `/root/Yard/Garden/Garden Tile` + `/root/Yard/Garden/Plants` (TileMapLayers — the dirt patch)

**`yard_collisions.gd`** — procedural at `_ready`:
- Reads wall TileMapLayers (HouseWalls, House/Layer1/Layer2/hoceag, BarnBody/Layer1, Magazie, Fence, BarnFence — configurable via `wall_layer_paths` export)
- For each used cell, samples the tile's atlas image, computes the alpha bbox, and spawns a `StaticBody2D` + `CollisionShape2D` rect sized to the opaque pixels (cached by `source_id:atlas.x,atlas.y`). Result: pixel-tight collision (fence top blocks only its visible top strip).
- Roof layers (BarnRoof, House/acoperis, rooffereastra, Layer3, Layer4) **explicitly excluded** so player walks behind them.
- 533 shapes total. One-time cost at scene load.

**`yard_zones.gd`** — three responsibilities:
1. **Garden interaction zone** — `Area2D GardenZone` auto-sized to `Garden/Garden Tile` used-cell bbox. On `body_entered` (player group): `Elias.set_zone("garden")` + shows `[E] Tend the garden` prompt (CanvasLayer Label, bottom-center). Hides on exit.
2. **E-press opens overlay** — connected to `Elias.interact_pressed` signal. Instantiates `Garden.tscn` (hidden state manager) + `GardenOverlay.tscn` (modal UI), calls `overlay.init(garden)`. Closes restore the prompt.
3. **Crop sprite rendering on yard** — listens to `garden.crop_planted` and `garden.garden_changed`. Spawns `Sprite2D` children of `Garden/Garden Tile/CropSprites` (y_sort enabled) with `AtlasTexture` regions into `Pixel Crawler/Environment/Props/Static/Farm.png`. **Each logical plant = 2×2 yard tiles**, sprite anchored at the inner 4-tile junction `(_garden_origin_tile + pos*2 + 1) * tile_size` — matches cauliflower-style `(8,8)` texture_origin pattern.

**`CROP_ATLAS` mapping (provisional, in `yard_zones.gd`)**:
- `turnip` → row 3, cols [2,3,5,7,8] (SEED/SPROUT/BLOOM/HARVEST/WILT). User confirmed row.
- `tomato` → row 1 (placeholder, user hasn't confirmed)
- `pumpkin` → row 5 (placeholder, user hasn't confirmed)
- All non-tall. Tall crops (garlic row 13?) need `tall=true` + `size_in_atlas` later.

**`Constants.gd` change**: `GARDEN_COLS = 4`, `GARDEN_ROWS = 4` (was 8 and 6). `garden.gd::_build_initial_tiles` now uses `Constants.GARDEN_COLS` instead of hardcoded `range(5)`. Back-field unlock code (`pos.x >= 5`, `unlock_back_field()`) is dead but harmless.

**`elias.gd` change**: added `Input.is_action_pressed("move_*")` checks alongside `ui_*` + raw `KEY_A/D/W/S`. Pure addition; lets MCP input.sequence drive him for testing.

**What's NOT done on the Yard** (next steps):
- [ ] Real atlas mapping for `tomato`/`pumpkin` (user must point at Farm.png rows)
- [ ] Tall crops (garlic row 13) — `tall=true` + `size_in_atlas (1,2)` in CROP_ATLAS
- [ ] TileSet texture_origin fix for hand-painted Plants cells. Only row 9 cols 2-5 (cauliflower) currently has `texture_origin = (8,8)` in `TileSetAtlasSource_yrlxp` (source id 3 of `TileSet_lwiud` embedded in yard.tscn at line ~8529). Cabbage etc. painted by hand render in single tile. Need one-shot Python/sed pass adding `texture_origin = Vector2i(8, 8)` to crop atlas coords.
- [ ] House door zone (Area2D on farmhouse door → [E] enters interior → bed advances DayManager). Currently no transition from yard to farmhouse.
- [ ] HUD overlay on Yard (day/gold/stamina/hunger).
- [ ] DayManager + TimeManager wiring — neither drives anything in the new Yard yet. SkyRect tint, day phase advancement, etc. unhooked.
- [ ] Continue with `2.0`/`2.1` etc. below as adapted to the Yard.

**Phantom error in editor logs** (ignore): `farmhouse.gd:89 TimeManager not declared`. Game runs fine; autoload is registered. `--script` flag bypasses autoloads, so `godot --headless --check-only --script <file>` will reproduce it. Stale editor parse cache.

**MCP testing gotchas** (apply to all future Godot work via MCP):
- `mcp__godot__node.update` on a running game writes through to the scene resource, **not** runtime state. Used it to teleport Elias for collision testing — permanently moved his spawn until I reverted + re-saved. Never use `node.update` for runtime poking; attach a debug script or drive via `Input` actions instead.
- `mcp__godot__editor.get_log_messages` doesn't capture `print()`. Use `push_warning`/`push_error` or look at stdout via Bash if you need diagnostic output.
- No mouse-click injection in MCP. Can't drive GardenOverlay's tool buttons. User has to playtest UI interactions; I can only set up the world for them.

### 2.0 — Pre-phase cleanup
- [ ] **2.0.1** Wire Farm → Farmhouse transition. Add Interactable area near Farm.tscn's `FarmhouseCollider` door region, on interact call `get_node("/root/Main").go_to_farmhouse()`. Mirror reverse in `farmhouse.gd` (Door already wired to `exit_requested` signal — needs Main listener)
- [ ] **2.0.2** Move farmhouse bookshelf lines from `farmhouse.gd::BOOKSHELF_LINES` to `content/npc_dialogue.json` under `"bookshelf": {"lines": [...]}` key. Update `farmhouse.gd::_on_bookshelf_interact` to pull from `DialogueManager`
- [ ] **2.0.3** Delete unused Cardinal NPC: `scenes/npcs/Cardinal.tscn` + `scenes/npcs/cardinal.gd`. Grep for references first, fix if any remain

### 2.1 — Day 1 opening + tutorial
- [ ] **2.1.1** Create `scenes/ui/tutorial.gd` + `Tutorial.tscn`. CanvasLayer overlay with a single `Label` for tooltip text. Auto-hides when not in active step
- [ ] **2.1.2** Tutorial trigger: subscribe to `DayManager.day_started`. If `day == 1 and not tutorial_complete` → start sequence
- [ ] **2.1.3** Opening sequence (Bible §Part 10 Day 1): black screen 2s silence → `AudioManager.play_music_layer("piano")` → fade-in farm at dawn → 5s breathing room → Elias on porch
- [ ] **2.1.4** Sequential tooltips (5s timeout or movement triggers next): "Use E to interact. Start with the soil." → "Select tomato seeds" → "Refill at the well" → "Water all 9 tiles"
- [ ] **2.1.5** First-watering-complete trigger: when all 9 plot tiles get their first water, spawn simultaneous sparkle particle on all 9 + `AudioManager.play_sfx("grace_note")` (one-shot)
- [ ] **2.1.6** Set `tutorial_complete = true` after final tooltip dismissed; tooltips never reappear
- [ ] **2.1.7** Bind interact key. Currently the project uses mouse clicks on Area2D — Bible spec is "E to interact". Either add `interact` action to project input map and route via Elias, OR keep mouse-only and update tooltip text accordingly

### 2.2 — Day 2 living world
- [ ] **2.2.1** Verify Bible Day 2 journal entry plays at night (already authored in `journal_entries.json`). Just confirm no tutorial relapse
- [ ] **2.2.2** Confirm CropPlot growth visual progresses from seed → sprout sprite on day rollover (read existing `garden/crop_tile.gd`)
- [ ] **2.2.3** No events should fire Day 2 except `narrator_morning_peace` — confirm `events.json` only has that entry

### 2.3 — Day 3 wilt + first harvest
- [ ] **2.3.1** Review `crop_tile.gd` wilt visual. Bible wants "quiet response, no accusation" — paler green + slight droop, NO popup. Refactor if current is too aggressive
- [ ] **2.3.2** Exploration reward: place carrot seed packet sprite in shed area on Day 1 (findable, not in tutorial). If player plants Day 1, harvest available Day 3
- [ ] **2.3.3** Confirm harvest SFX (`harvest_shake` + `coin_pop`) feels tactile — Bible spec: "gentle pop and tumble"

## Files touched (expected)
- `scenes/world/Farm.tscn` (interactable door area)
- `scenes/farmhouse/farmhouse.gd` (move BOOKSHELF_LINES)
- `content/npc_dialogue.json` (add bookshelf block)
- `scenes/ui/tutorial.gd` + `Tutorial.tscn` (new)
- `scenes/main.gd` (wire farmhouse exit signal)
- `scenes/world/farm.gd` (tutorial overlay integration)
- `scenes/garden/crop_tile.gd` (wilt visual review)
- `project.godot` (input map `interact` if added)
- Delete: `scenes/npcs/Cardinal.tscn`, `cardinal.gd`

## Verification (per CLAUDE.md: smoke tests)
- [ ] Open Godot, run Main scene → reaches Farm → tutorial fires
- [ ] Walk through all tutorial steps in order → grace note + sparkle at watering
- [ ] Sleep → Day 2 → no tutorial repeats
- [ ] Sleep → Day 3 → unwatered tile wilts (subtle), carrots harvestable if planted
- [ ] Walk to farmhouse door → enters interior → exit door returns to farm

## Open questions before starting
1. Keep mouse interaction OR add E key? (Bible says E, existing code uses mouse)
2. Sparkle particle: GPUParticles2D real, or simple Tween color flash on tiles? (Asset budget)
3. Tutorial style: persistent tooltip panel OR transient toast notifications?
