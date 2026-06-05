# Yard Depth Sorting + Fence/Building Occlusion & Collision

> Canonical reference for how the player, fences, buildings, ground and trees
> draw over/under each other in `scenes/world/yard.tscn`, plus the fence/roof
> collision. Built across the 2026-05-29 → 2026-05-30 sessions.
> **All of it is runtime/script-only — `yard.tscn` is NOT modified.** Two files:
> `scenes/world/yard_loop.gd` (depth) and `scenes/world/yard_collisions.gd`
> (colliders).

## ⚠️ START HERE — open issue for the next session

**Symptom (user, 2026-05-30):** the **horizontal SOUTH fences** (notably the
**leftmost tiles of the barn-yard bottom rail**) don't occlude Elias — he draws
*over* them. Collision stops him fine; it's the draw order. "The rest of the
fences work." Vertical fences and roof occlusion are CONFIRMED good.

**⚠️ Update 2026-05-30 (later) — 2nd attempt, STILL BROKEN, do NOT repeat:**
A fresh chat re-attacked this **without reading this page first** and burned the
whole session on two wrong tracks:
1. Treated it as fence **geometry** — trimmed the barn-yard bottom-left stub,
   added then removed an experimental west edge. Not the issue.
2. Then edited **`yard.tscn` directly**: added `y_sort_enabled = true` to the
   `Yard` root, to `Fence` and `BarnFence` (+ their `layer_N/y_sort_enabled`), and
   `z_index = 5` to `Vegetation`, `BarnBody`, `BarnRoof`, `BarnDoor`.
   **These are redundant with `yard_loop.gd`'s runtime z-banding (it sets
   Z_TREES=20, Z_BUILDING=10, fence Y-sort with `y_sort_origin=16` at `_ready`),
   which OVERRIDES them — so they changed nothing. User: "still not fixed."**
   → **Next session: REVERT those tscn edits** — depth is script-only by design
   (see the invariant in the header). The Godot MCP bridge dropped repeatedly
   again (same blocker #1).
- **Net real change still in `yard.tscn`:** the barn-yard bottom rail lost its
  `x4,y23` `(4,27)` stub tile (now `x5–14`, ending at the dirt SW corner). Minor;
  keep or restore. The pen's open west side (y21–22, below the house) is the
  intended entrance — leave open.
- **Lesson:** "player draws on top of / doesn't get overlapped by fence" is a
  **DEPTH / Y-SORT** problem owned by `yard_loop.gd`, never tile geometry. Read
  this page first. Don't edit `yard.tscn` for depth.

**Could not be verified or finished because of two hard blockers this session:**
1. **Godot MCP died** — another MCP client (BLACKBOX in the user's VS Code)
   grabbed the godot-mcp connection; mine was terminated ("this server is no
   longer active") and would not reconnect mid-session. So I could not drive the
   game / screenshot to diagnose.
2. **Project is in OneDrive** — Godot often fails to detect external file edits
   there, so `Project → Reload Current Project` may serve **stale code**. Several
   of my fixes may never have actually run. This likely explains "no you didn't
   fix it."

**First moves next session (fresh chat, MCP reconnected, ideally project copied
to e.g. `C:\Games\PaleGarden`):**
1. `mcp__godot__godot_editor get_state` to confirm the bridge is live.
2. Run the game, drive Elias (`ui_left/right/up/down`) to the **barn-yard bottom
   rail, left end**, screenshot. Confirm whether the fence draws over his shins.
3. If NOT occluding, check the actual cause (3 hypotheses, in order of
   likelihood):
   - **(a) Stale code** — verify the running build matches disk (the fixes below
     are all on disk). If on a non-OneDrive copy this disappears.
   - **(b) `y_sort_origin` not applying to the legacy `TileMap` fence** —
     `_enable_tile_ysort` calls `set_layer_y_sort_origin(i, 16)` on the legacy
     `Fence` TileMap. If that doesn't actually shift the sort, the fence sorts
     from its TOP and Elias (feet south of the cell top) draws over it. **Fix:**
     set per-tile `y_sort_origin` in the TileSet, OR (better) convert `Fence` to
     a `TileMapLayer` where `y_sort_origin` is a real property.
   - **(c) `occlude_front_band` still reaches the rail** — if the rail sits
     within `36px` south of the barn's `base_y` AND under the barn's x-span, the
     player flips to `Z_FRONT (11)` there and rides over the fence. (But in the
     user's last shot he looked east of the barn x-span, so (a)/(b) are more
     likely.) Lower `occlude_front_band` or see the deeper fix below.

**Deeper/real fix (removes all the tuning):** the legacy `TileMap`s — **Magazie,
Fence, Vegetation** — are the root of every hard case. Whole-object building z
can't be both above a fence behind it and below a fence in front of it; that's
why buildings use a fixed z + a player-flip hack instead of sorting at their
base. **Convert those three legacy `TileMap`s to `TileMapLayer`s**, give the
buildings a base `y_sort_origin`, and the whole scene sorts per-tile with no
bands, no player-flip, no `occlude_*` knobs.

## What's CONFIRMED working

- **Roof occlusion (all buildings)** — Elias correctly hidden behind House/Barn/
  Magazie roofs when north of them, draws over walls at the door. (user img, the
  big early win.)
- **Vertical fences solid** — can't straddle/stand-in them. (`MODE_SOLID`.)
- **Walk UNDER the Magazie roof** — roof tiles no longer collide; only the bottom
  wall rows do.
- **Most horizontal fences** occlude when Elias stands north of them.

## The depth model (`yard_loop.gd::_setup_building_occlusion` + `_process`)

Yard root has `y_sort_enabled = true`. Everything is placed in **z bands**
(`z_index` dominates sort; Y only orders WITHIN a band):

| Band | z | Who | Set where |
|------|----|-----|-----------|
| `Z_GROUND` | -100 | Grass, Path, BarnGround, Garden, Structures, Objects | `_GROUND_PATHS` loop |
| `Z_FENCE` / `Z_PLAY` | 0 | **fences + the player** — interleave by Y here | fences via `_enable_tile_ysort`; player default |
| `Z_BUILDING` | 10 | House, Barn(Body/Roof/Door), Magazie — FIXED, always over fences (→ no fence-over-roof) | `_register_occluder` sets each node |
| `Z_FRONT` | 11 | the **player** when standing in front of a building | `_process` |
| `Z_TREES` | 20 | Vegetation — above everything (prior look) | `_TREE_PATHS` loop |

**Player flip (`_process`, every frame):** `z = Z_FRONT` when Elias is within a
building's x-span **and** `base_y <= feet.y <= base_y + occlude_front_band`;
else `z = Z_PLAY (0)`. The band exists so he rides over the building's front
walls/porch ONLY while overlapping it, then drops into the fence band so yard
fences occlude him. `_register_occluder` stores `{base_y, x_min, x_max}` per
building (x-span from the walls layer's `get_used_rect`, padded by
`occlude_x_pad`; `base_y` from `_footprint_base_y`).

**Why building z is fixed + player flips (not building flips):** a building that
flips its own z (`-1`/`+1`) lands BELOW fences when "in front," so a fence behind
it paints over its roof (the user's earlier "fence covers house" bug). Pinning
buildings above fences and flipping the player instead fixes that — at the cost
of the `occlude_front_band` edge case above.

### Tuning knobs (Inspector → `YardLoop` node)
- `occlude_front_band` (**36.0**) — how far south of a building the player still
  rides above it. Too big → floats over yard fences; too small → pops behind the
  porch. Shallow barn yard makes this tight.
- `occlude_x_pad` (16.0) — widens the in-front x-span so the player draws over
  porch pillars sticking past the walls.
- `house_occlude_y_offset` (0.0) — nudges the base line.

## Fence + roof collision (`yard_collisions.gd`)

Builds `StaticBody2D` colliders from `wall_layer_paths`. Per-cell **mode**:

| Mode | shape | used for |
|------|-------|----------|
| `MODE_TIGHT` (0) | alpha bbox of the tile | walls/buildings |
| `MODE_SOLID` (1) | full cell | fence **vertical** run (no straddle) |
| `MODE_BASE` (2) | thin `6px` strip at the cell **foot** | fence **horizontal** run (walk up so it overlaps shins) |

`_cell_mode` picks the mode; `_is_vertical_run` checks neighbours (vertical
neighbour + no horizontal = vertical run). Fences are flagged by
`solid_collision_paths = [Fence, BarnFence]`.

**Roof-passable buildings:** `roofed_building_paths = [Magazie]`,
`roof_building_wall_rows = 3` → for the Magazie (a legacy `TileMap` holding walls
+ roof in one node), only the bottom 3 rows get colliders so you can walk under
the eaves. House/Barn still collide their roof layers (named directly in
`wall_layer_paths`) — same mechanism could cover them if wanted.

## Fence `y_sort_origin` (the suspect for the open bug)

`_enable_tile_ysort(path)` sets, on each fence: node `z_index = 0`,
`y_sort_enabled = true`, and per internal layer `set_layer_y_sort_enabled(i,true)`
+ `set_layer_y_sort_origin(i, tile_height=16)`. The origin pushes the fence's
sort point to its FOOT so it counts as "in front of" Elias only once he's south
of the foot — i.e. it draws over his shins when he walks up. **If the open bug is
(b), this is the line that isn't taking effect on the legacy TileMap.**

## Session history of approaches (so we don't repeat dead ends)
- **Building z-toggle** (per building `-1`/`+1` by player Y): fixed roofs, but
  caused "fence covers house." Abandoned.
- **Wrap each building in a base-anchored `Node2D` sorter:** sorters were created
  at the right base Y (verified via debug) but the building still drew at its own
  node Y — a non-Y-sorted Node2D sorter did NOT sort its legacy-TileMap subtree
  as a unit. **Dead end for legacy TileMaps.** (Might work once they're
  `TileMapLayer`s.)
- **Current:** fixed building z + player-flip + per-tile fence Y-sort. Works
  except the shallow-yard fence case above.

## Related
- [[../../../todo/PaleGarden-todo]] — top "Active" has the next-session checklist.
- [[../../../mistakes]] — OneDrive stale-code + single-client MCP gotchas.
