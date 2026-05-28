---
project: The Pale Garden
type: mechanics index
last_updated: 2026-04-30
---

# Mechanics — Implemented Systems

## Player movement
`scenes/world/elias.gd` — `CharacterBody2D`. WASD or arrow keys. SPEED = 80 px/s. `move_and_slide()` for collision. Walk-bob = `sin(_anim_t * 12) * 1.5` y-offset on body+head. `_facing : int` shifts eye position. `_draw()` = bone-coloured body+head with dark outline + 2 pixel eyes + shadow.

## Interaction system
- `_current_zone : String` set by farm.gd when entering `HouseDoorZone` / `MarketGate` / `GardenZone` Area2Ds.
- Press `KEY_E` → emits `interact_pressed(zone_id)` signal.
- `farm.gd._on_elias_interact(zone_id)` dispatches: `house` → journal entry, `market` → travel (only Days 7/14), `garden` → opens GardenMenu.
- `_prompt_label` Label in CanvasLayer shows context-sensitive prompt.

## Garden — `[E]` Menu Pattern
- `scenes/ui/GardenMenu.tscn` + `garden_menu.gd` — modal CanvasLayer (layer 12) with dark dim overlay + center panel.
- 4 tool cards: TILL / WATER / PLANT / HARVEST. Each card disabled when `GameState.stamina < cost`.
- `tool_selected(name)` signal → farm.gd sets `_garden.active_tool` and shows feedback prompt.
- ESC or E closes the menu.

## Garden tile system
- `scenes/garden/garden.gd` — 5×6 grid (cols 0–4) at start, expands to 8×6 after `back_field_expand` event (Day 2).
- `_tile_states : Dictionary[Vector2i, String]` with values "empty" | "tilled" | "planted".
- `_draw()` paints colored rects per state + 1px border. Hover highlight shows white pulse + COLOR_BONE border.
- Click handling uses `to_local(get_global_mouse_position())` (Garden node is positioned at world (64, 384)).
- Each action (`_till_tile`, `_plant_seed`, `_water_tile`, `_try_harvest`) checks and consumes stamina.

## Stamina
- `GameState.stamina : int` (max = `Constants.STAMINA_MAX = 6`).
- Each garden action costs 1 (`Constants.STAMINA_TILL/WATER/PLANT/PICK`).
- HUD: 6 ColorRect dots (8×8) — yellow when filled, dark when spent.
- Restored to MAX on `DayManager.advance_day()`.
- When stamina = 0, `time_of_day.gd` enters night phase and shows "The day is over" prompt.

## Time of day
- `scenes/world/time_of_day.gd` — Node listening to `GameState.stamina_changed`.
- 4 phases: morning / noon / evening / night. Advances every 3 actions.
- Tweens `WarmOverlay/WarmRect.color` (1.5s) between phase tints.
- On sleep → resets to morning. On entering night → locks tools.

## Crop lifecycle
- `scenes/garden/crop.gd` — Node2D with `phase`, `crop_type`, `watered`, `has_weed`.
- `crop_type` ∈ {"turnip", "tomato", "pumpkin"} drives ripe-fruit color and harvest gold (3/8/15g).
- Phases (driven by `DayManager.day_ended`): SEED → SPROUT → BLOOM → HARVEST → WILT.
- Each phase requires `watered = true` to advance; unwatered seed → has_weed; HARVEST unpicked → WILT.
- `_draw()` renders distinct visuals per phase.

## Inventory
- `GameState.crops_inventory : Dictionary` keyed by crop type.
- `GameState.seeds_inventory : Dictionary` keyed by crop type. Starts with 3 turnip seeds.
- HUD `Inventory` Label shows `T:N M:N P:N`.
- `consume_seed(type)` returns false if none — blocks planting.

## Day cycle
- `DayManager.advance_day()` — emits `day_ended`, decrements hunger, increments day, restores stamina, resets time of day, fires day events from `events.json`, emits `day_started`.
- Triggered by Rest → Journal → "sleep" button.

## Tutorial
- `farm.gd._maybe_fire_tutorial()` runs on `_ready()` if `current_day == 1`.
- After 2-frame defer, calls `DialogueManager.start_dialogue("narrator", "tutorial_till")` and unlocks all tools.

## Map architecture
- World: 640×640 px, viewport 640×360. Camera2D limits at map bounds.
- Drawn entirely in `scenes/world/farm_ground.gd._draw()` — forest borders + 30 trees + grass + 15 flowers + dirt field + 3 garden patches + farmhouse (roof, walls, porch, steps, door, windows, chimney with smoke) + well + mailbox + scarecrow + fences + market road + sign post.
- All positions baked into `const` arrays — deterministic.

## Camera
- `Camera2D` is child of `Elias`. `position_smoothing_enabled = true`, smoothing speed 5.0.
- Limits: 0/640/0/640.

## Collisions
- `FarmhouseCollider` StaticBody2D with 256×208 RectangleShape2D at world (320, 184).
- Elias collision: 12×20 box.
- No other static collisions yet (forest visuals not collidable).
