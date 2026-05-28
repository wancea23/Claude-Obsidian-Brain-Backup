# Garden Grid

## Layout
- 8 columns × 6 rows, 32px tiles (expanded to 40px in GardenOverlay)
- Total 48 tiles; back field (cols 5–8) locked until Day 6

## Tile states
- `empty` — untouched
- `tilled` — hoed, ready to plant
- `planted` — contains a crop node

Stored in `_tile_states: Dictionary` keyed by `Vector2i(col, row)` in `garden.gd`.

## Back field unlock
- Triggered by Day 6 event `back_field_expand` (events.json)
- `GameState.back_field_unlocked` flag gates access
- GardenOverlay greys out back-field tiles until unlock

## Rendering
- `GardenDisplay` (inside GardenOverlay) redraws each frame from:
  - `Garden.get_tile_states()` — returns the `_tile_states` dict
  - `Garden.get_crop_phases()` — returns phase per tile for colored overlays
- Tile hover: pulse highlight drawn in GardenDisplay._draw()

## Interaction flow
1. Player presses E inside the garden zone
2. `GardenOverlay` opens (CanvasLayer 10)
3. `GardenDisplay` handles mouse clicks → calls `Garden.till()`, `Garden.plant()`, etc.
4. Each action emits `garden_changed` → GardenDisplay queues redraw
