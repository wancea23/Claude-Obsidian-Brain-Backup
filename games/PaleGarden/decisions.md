---
project: The Pale Garden
type: game design decisions log
last_updated: 2026-04-30
---

# Decisions Log

Why things are built the way they are.

## 2026-04-30 — Act 1 uses warm green palette, NOT the gothic dark palette
**Why:** STYLE.md prescribes a dark gothic palette (`COLOR_BG = #1a1410`) for the whole game. Story bible (story-sketch.md) says Act 1 is "Warm pixel palette — amber, green, soft brown… Players need to love this world before it breaks." User explicitly confirmed: "Act 1 has to have greenish colors, the colors of redish only after the blood plant appears."

**Decision:** Added a separate `COLOR_ACT1_*` palette block to `globals/Constants.gd`:
- `COLOR_ACT1_SKY = (0.60, 0.75, 0.88)` — soft morning blue
- `COLOR_ACT1_GRASS = (0.35, 0.55, 0.22)` — proper warm green
- `COLOR_FOREST = (0.14, 0.28, 0.08)`
- Garden soil / house / porch in warm browns and greys

The dark/gothic palette stays for UI text and Acts 2–5. Reviewer must NOT replace Act 1 colors with the gothic ones.

## 2026-04-30 — Garden interaction is `[E] menu`, not direct click
**Why:** User feedback: "I would like to get close to it and press E in order to interact and the menu from the lovable preview will appear and be able to plant water harvest". Direct-click + HUD-tool-button flow felt clunky and didn't communicate cost.

**Decision:** Walk into `GardenZone` Area2D → `[E] Tend the Garden` prompt → modal `GardenMenu.tscn` opens with 4 tool cards. Each card shows label, description, and is auto-disabled when `GameState.stamina < cost`. Selecting a tool sets `_garden.active_tool` and closes the menu; player still clicks tiles to apply the tool. ESC/E closes the menu.

The HUD tool buttons remain for direct selection but the menu is the primary interaction.

## 2026-04-30 — Stamina (6 actions/day) drives day pacing
**Why:** No mechanism existed to make Days feel like days — sleep was optional and meaningless. Stardew-like stamina creates a natural rhythm and gives Rest emotional weight.

**Decision:** `GameState.stamina` (max 6). Each garden action costs 1. Stamina dots in HUD top-bar dim left-to-right as spent. On `DayManager.advance_day()`, stamina is restored to MAX. When stamina hits 0, all garden tools auto-disable and `time_of_day` enters night phase.

## 2026-04-30 — Time-of-day tied to action count, not real-time
**Why:** A real-time clock would break the cozy pacing — players might feel pressured. Tying phases to actions (every 3 actions = phase advance) keeps it tactile.

**Decision:** `time_of_day.gd` listens to `stamina_changed`. After every `Constants.ACTIONS_PER_PHASE = 3` actions: morning → noon → evening → night. WarmOverlay ColorRect tweens between phase tints over 1.5s. Night locks tools and shows "The day is over" prompt.

## 2026-04-30 — NPCs are event-driven, not ambient
**Why:** User: "Margaret or whatever NPC you placed should not exist on the farm." Ambient NPCs muddy the story beats — Margaret should *appear* on Day 3 (fence sidequest), not just be standing around.

**Decision:** `farm.gd._spawn_ambient_npcs()` only spawns Bruno (and only if `current_day >= 4`). Margaret and The Seller are spawned exclusively by `farm_sidequests.gd` on their event days.

## 2026-04-30 — Crop variety as 3-color placeholder, not 3 entities
**Why:** Need crop variety for market economy without inventing 3 separate crop classes / tilesets. With no sprites, the visual difference is the ripe-fruit color.

**Decision:** Single `Crop` class with `crop_type : String` field. `_draw()` paints same stem/leaves but the ripe fruit rect uses `TYPE_COLOR[crop_type]` (turnip=cream, tomato=red, pumpkin=orange). Harvest gold lookups `TYPE_PRICE[crop_type]` (3/8/15g). When tomato/pumpkin seeds unlock at market, no new code needed — just add to `seeds_inventory`.

## 2026-04-30 — Map drawn with `_draw()` rects, not TileMap
**Why:** TileMap requires a configured TileSet resource. With no sprites yet, configuring a TileSet for placeholder colors is wasted work. `_draw()` is fast, deterministic, and easy to swap to TileMap later.

**Decision:** `farm_ground.gd._draw()` paints all world geometry (forest, grass, soil, house, props, fences, garden patches). `garden.gd._draw()` paints the 32×32 tile grid. `crop.gd._draw()` paints crop visuals. When sprite assets arrive, replace `_draw()` per-class without touching scene structure.

## 2026-04-30 — Map is 640×640 with vertical scroll only
**Why:** Viewport is 640×360 (config'd in project.godot). 640-wide map = no horizontal scroll = simpler camera. 640 tall = ~280px of vertical scroll = enough for forest top, farmhouse, dirt field, gardens, market road.

**Decision:** Camera2D limits clamped to `(0,0)–(640,640)`. Player spawns at (320, 300) — bottom of farmhouse steps. Trees, decoration, and props all positioned in a fixed deterministic array baked into `farm_ground.gd` so re-runs look identical.

## 2026-04-30 — Day 1 tutorial fires on first farm load, not via DayManager event
**Why:** `DayManager._fire_day_events()` only runs when `advance_day()` is called. On a fresh save / first launch, the player enters Day 1 without ever advancing. The `tutorial_start` event in events.json never fires.

**Decision:** `farm.gd._maybe_fire_tutorial()` runs in `_ready()`. If `current_day == 1`, deferred 2 frames, calls `DialogueManager.start_dialogue("narrator", "tutorial_till")` and unlocks all tools. Subsequent days don't re-trigger because `current_day != 1`.

## 2026-04-30 — Empty world fix: base ground rect prevents sky bleed
**Why:** Forest borders + grass + dirt left small gaps between drawn zones. The Background CanvasLayer (sky color) showed through the gaps as visible blue/green stripes.

**Decision:** `farm_ground.gd._draw()` first paints a 640×640 base rect of `COLOR_ACT1_SOIL` before any zone-specific rect. All gaps now show brown soil instead of sky.
