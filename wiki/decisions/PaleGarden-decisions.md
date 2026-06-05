# PaleGarden — Decisions

## 2026-05-30 — Top-down depth: fixed building z + flip the PLAYER (not the building)

**Why**: A whole building's single `z_index` cannot be simultaneously *above* a
fence behind it and *below* a fence in front of it. The first attempt — flip each
building's z `-1`/`+1` by the player's Y — fixed roofs but made a fence behind a
building paint over its roof ("fence covers house"). So buildings are pinned at a
**fixed** `Z_BUILDING (10)`, always above fences (`Z_FENCE 0`) → no fence-over-
roof, ever; and instead the **player** flips to `Z_FRONT (11)` only while in
front of a building (within its x-span and within `occlude_front_band` south of
its base). Fences + player share the `z=0` Y-sort band so fences occlude the
player per-tile. Net: roofs occlude, fences occlude, no fence-over-roof — without
rebuilding the scene.
**Alternatives considered & rejected**: (1) Building z-toggle — fence-over-roof
bug. (2) Wrap each building in a base-anchored `Node2D` sorter so it Y-sorts at
its base — **verified the sorters sat at the right Y but the legacy `TileMap`
buildings still drew at their own node Y**; a non-Y-sorted Node2D didn't sort its
legacy-TileMap subtree as a unit. Dead end *for legacy TileMaps*. (3) Full per-
tile Y-sort everywhere — the correct end state, but blocked until **Magazie /
Fence / Vegetation are converted from legacy `TileMap` to `TileMapLayer`**.
**Known limitation**: the player-flip needs `occlude_front_band` tuned per scene
— a fence sitting very close behind a building (the shallow barn yard) can fall
inside the band and get floated over. The permanent fix is the TileMapLayer
conversion. Full detail + the still-open south-fence bug:
[[../games/PaleGarden/implementation/yard-depth-sorting]].
**Affects**: `scenes/world/yard_loop.gd` (`_setup_building_occlusion`,
`_register_occluder`, `_process`, `_enable_tile_ysort`), `scenes/world/yard_collisions.gd` (per-cell fence collider modes + roof-passable buildings).

## 2026-05-29 — Yard day loop as a child-node coordinator (`yard_loop.gd`), not the root script

**Why**: The `Yard` root already has `yard_tool.gd` (a `@tool` procedural map builder) attached — replacing it to host the day-loop wiring was off the table. The established pattern in this scene is already "one procedural coordinator per concern as a child Node2D": `Collisions`/`yard_collisions.gd` and `Zones`/`yard_zones.gd`. So the day loop is a third sibling, `YardLoop`/`yard_loop.gd`, building HUD + journal + day-transition + warm-overlay/tint + house rest zone procedurally in `_ready`. Net scene change: one node + one `attach_script` (done via Godot MCP so the editor stayed in sync). Keeps `yard.tscn` (~14k lines) un-hand-edited and the wiring regeneratable.
**Alternatives considered**: Merge into `yard_tool.gd` (mixes a `@tool` map builder with runtime UI — bad separation, and `@tool` would try to run the UI in-editor). Author HUD/zones as `.tscn` nodes (hand-editing the giant scene; brittle to redesigns).
**Affects**: `scenes/world/yard_loop.gd` (new), `/root/Yard/YardLoop` node. Exports `elias_path`, `house_walls_path`, `house_door_offset_tiles`. Reuses the `farm.gd` rest→`Journal`→`DayManager.advance_day`→`DayTransition` flow.

## 2026-05-29 — House rest zone spans the full frontage, not the door

**Why**: `House/HouseWalls` is a **solid rectangle** — the visible door is decorative art on a different layer, so there's no missing-cell "doorway" to detect (the code's bottom-up row gap-scan finds nothing and falls back to footprint centre). Centring a small zone on the geometric centre missed the off-centre door; the only way to hit the actual door would be a hardcoded "+4 tiles" offset — exactly the magic-number fragility the [[#2026-05-28 — Tight per-pixel collision via alpha bbox, not whole-tile rects|collisions decision]] avoided. So the rest zone covers the **whole house frontage** (footprint width × 3 tiles, one tile below the wall base), and the always-available HUD **Rest** button is the primary rest path. `house_door_offset_tiles` export remains for manual tuning, and the gap-scan still biases toward a real door if a future house has one.
**Alternatives considered**: Hardcoded door offset (brittle per-house magic number). Detect the door from a separate art layer (which layer holds it is unknown/unstable). Door-interior transition scene (more scope than the loop needs; rest opens the diary in place for now).
**Affects**: `yard_loop.gd::_build_house_door_zone()`, `HouseDoorZone` Area2D under `YardLoop`.

## 2026-05-28 — Yard collisions: procedural StaticBody2D, not TileSet physics layer

**Why**: The yard's wall TileMapLayers (HouseWalls, BarnBody, Magazie, Fence…) don't have a `physics_layer` configured on their TileSets, and bulk-editing per-tile collision polygons via the embedded TileSet inside `yard.tscn` (~14k lines) is fragile and editor-bound. A `_ready`-time procedural generator that reads `get_used_cells()` and spawns `StaticBody2D` + `CollisionShape2D` rects per cell is one script, zero TileSet edits, easy to regenerate when walls are repainted.
**Alternatives considered**: Configure `physics_layer` + per-tile polygons in TileSet editor (tedious, ~hundreds of tiles); hand-author colliders in the .tscn (doesn't scale to redesigns).
**Affects**: `scenes/world/yard_collisions.gd`, `Yard/Collisions` child of yard.tscn. Roof layers are excluded by explicit allowlist — adding a new wall layer requires editing `wall_layer_paths` in the script.

## 2026-05-28 — Tight per-pixel collision via alpha bbox, not whole-tile rects

**Why**: Whole-tile colliders hold the player half a tile away from thin sprites (fence top strip, log rows). Reading each tile's atlas image once, computing the opaque bbox, and sizing the `RectangleShape2D` to those bounds gives pixel-flush collision with no TileSet edits. The bbox is cached per `(source_id, atlas_coord)` so 533 cells reuse a handful of unique scans.
**Alternatives considered**: Per-tile custom polygons in TileSet (editor work + brittle); hand-tuned shrink factors per layer (fence=4px high, wall=full, etc — magic numbers + breaks on art changes).
**Affects**: `_tight_bbox()` in `yard_collisions.gd`. Cost is one-time at scene load.

## 2026-05-28 — Crop sprites on yard, not Plants TileMap painting

**Why**: User wants planted crops to appear on the yard as the GardenOverlay logical state changes. Painting cells into `Garden/Plants` at runtime would need (a) per-crop tile data set up in the TileSet with `texture_origin = (8,8)` to center-on-corner, (b) tracking which atlas coord corresponds to which `(crop_type, phase)`, (c) tilemap repaints on every phase change. Spawning `Sprite2D` children with `AtlasTexture` pointing into `Farm.png` directly bypasses the TileSet entirely — origin/size handled in code, no editor work needed.
**Alternatives considered**: Drive `Plants` TileMapLayer from `garden_changed` (requires fixing every crop tile's `texture_origin` first); render in `Garden.gd`'s existing `CropContainer` (only visible inside the overlay's mini-grid, not on the yard).
**Affects**: `yard_zones.gd::_spawn_or_update_crop()`, `CropSprites` Node2D child of `Garden/Garden Tile`. Logical cell → world: `(_garden_origin_tile + pos*2 + 1) * tile_size` (each plant = 2×2 yard tiles, anchored on inner junction).

## 2026-05-28 — Garden grid 4×4, not 5×6

**Why**: Old `Garden.tscn` was authored for an 8-wide back-field-unlockable plot (`GARDEN_COLS=8`, `range(5)` initial). The new Yard's dirt patch fits 4×4 plants (8×8 yard tiles ÷ 2 tiles per plant). Shrinking the constants keeps overlay grid in sync with what's visible on the farm and avoids planting off the dirt.
**Alternatives considered**: Keep 5×6 + clamp planting to a visible window (extra UI logic for no gain).
**Affects**: `Constants.GARDEN_COLS=4`, `Constants.GARDEN_ROWS=4`, `garden.gd::_build_initial_tiles` now uses `GARDEN_COLS`. Back-field unlock (`pos.x >= 5`, `unlock_back_field()`) is dead code now but harmless.

## 2026-04-29 — Code/Games/ subfolder for agent isolation

**Why**: Putting `.claude/agents/gamedev/` directly under `Code/` would load gamedev agents into every school project (AA Labs, ASP Scrapper, ML, …). `Code/Games/` keeps them OneDrive-synced AND scoped — Claude Code only loads `.claude/agents/` from cwd's tree.
**Alternatives considered**: `~/.claude/agents/gamedev/` (truly global but not OneDrive-synced — would need to recreate per machine). Hybrid (agents global, tools synced) — more moving parts.
**Affects**: every gamedev agent path, the `Code/Games/CLAUDE.md` workspace config

## 2026-04-29 — File-mediated coordination, not real-time agent dialogue

**Why**: Subagents in Claude Code can't talk directly anyway — only the parent (Director) can spawn them via Task tool. File-mediated coordination (asset_requests.json, audio_requests.json, vault pages, review.md) is debuggable, leaves an audit trail, and survives session restarts. Real-time SDK message routing would be a multi-day side project before any actual game has been written.
**Alternatives considered**: Anthropic SDK + custom message broker. AutoGen integration. Both rejected as premature.
**Affects**: Director workflow, every agent's communication contract

## 2026-04-29 — ML venv outside OneDrive

**Why**: AudioCraft + diffusers + torch is ~5 GB. OneDrive syncing those wheels would be an absolute nightmare (slow sync, lock contention, version drift across machines). Venv at `~/gamedev-tools-venv/` (per-machine) bootstrapped from synced `requirements.txt`.
**Alternatives considered**: Per-game venv (5 GB × N games duplicated). Conda env with shared cache (still in user home, not synced).
**Affects**: `gamedev-tools/README.md` bootstrap, every ML invocation in artist + audio-engineer agents

## 2026-04-29 — Godot 4.3 + GDScript (not pygame, not C#)

**Why**: pygame would force the team to write a renderer + scene system from scratch. Godot 4's 2D renderer has CanvasGroup (shader-on-group, perfect for whole-garden pulse-on-hunger effect) and a much-improved TileMap with per-tile metadata (perfect for storing per-tile plant state). GDScript over C# because: faster iteration, no .NET SDK requirement, sufficient for 2D. User cited Godot 4.2+ being solid for 2D and the "less stable" rep being outdated for 2D-only projects.
**Alternatives considered**: pygame (rejected — too much engine work), Godot 4 + C# (rejected — slower iterate, .NET dep), Godot 3.5 (rejected — TileMap weaker, CanvasGroup absent).
**Affects**: architect.md (scaffolds project.godot), coder.md (GDScript syntax + TileMap + CanvasGroup), ui-agent.md (Control nodes), tester.md (godot --headless), reviewer.md ([GD3] flag for 3.x syntax)

## 2026-04-29 — Four endings, including a hidden one

**Why**: A hidden fourth ending ([[unmarked]]) gives players who notice the garden's pattern early a reason for a second playthrough. Three endings felt symmetric and predictable.
**Alternatives considered**: Three endings (cleaner but less replayable). Branching state inside one ending (technically simpler but less satisfying).
**Affects**: [[narrative/storyline-graph]], all four endings/*.md, reviewer's reachability check

## 2026-04-29 — Per-game vault under graphify-out/wiki/games/

**Why**: Game projects need richer documentation than a single project page can hold (storyline graphs, per-mechanic specs, per-ending state, per-character arcs). Nesting under `wiki/games/<Name>/` keeps the standard project page (`projects/PaleGarden.md`) as the global index entry while letting the game itself have its own multi-folder vault.
**Alternatives considered**: Single fat project page (unworkable for >2 games). Separate Obsidian vault entirely (loses cross-project navigation).
**Affects**: VAULT.md protocol, every agent's vault-integration section

## 2026-05-02 — Elias style pinned via a small LoRA

**Why**: SD 1.5's default pixel art is generic. The user supplied a 1024×1024 Elias reference sheet and wanted that exact style every time. A LoRA captures style faithfully on a small dataset and runs locally on existing hardware. Trained rank-8 DreamBooth LoRA on ~28 sliced reference cells, 1500 steps, fp16, ~22 min on a 3060 Ti. Final loss ~0.02–0.2.
**Alternatives considered**: IP-Adapter style transfer (too prompt-sensitive, drifts between sprites). Switching to a pixel-specialized base model like RetroDiffusion (more refactor, paid).
**Affects**: `gamedev-tools/loras/elias_palegarden/` (gitignored, per-machine), `gamedev-tools/lora_training/{prepare_dataset,train_lora}.py` (recipe). Trigger token `eliaspx`. Recipe is reproducible — drop more reference PNGs into `datasets/elias_palegarden/` and rerun `train_lora.py --clean`.

## 2026-05-02 — Sprite animation: AI base + procedural limb shifts

**Why**: First tried slicing the user's reference sheet directly into 6-frame strips. Result: visible "wobble" between frames because the reference's 6 cells are 6 *different drawings* of Elias, not a real walk cycle — head/face/eye pixels jitter independently of the leg motion. Then tried AnimateDiff + the LoRA at rank 1.6 — output collapsed into pastel mush; the rank-8 LoRA is too small to dominate the AnimateDiff motion module. Final design: generate ONE canonical Elias per view with SD+LoRA (`generate_elias_base.py`), freeze those PNGs, then animate by code (`animate_elias_base.py`): `out = base.copy(); shift(leg_pixels, ±dx); shift(arm_pixels, ∓dx)`. Guarantees pixel-identical head/torso/face across every frame in a strip; only the limb pixels we explicitly translate change.
**Alternatives considered**: Slice + foot-anchor align (kept code in repo for future hand-aligned references — see `slice_elias_reference.py` — but not used for Elias). AnimateDiff (failed). Hand-paint Elias from scratch (rejected by user — wanted AI generation).
**Affects**: `gamedev-tools/{generate_elias_base,animate_elias_base,make_walk_up_from_walk_down}.py`, `PaleGarden/assets/sprites/elias_*_strip.png`, `PaleGarden/scenes/world/elias.gd` (unchanged: still 32×48 frames, 5 anim rows).

## 2026-05-02 — Godot import cache must be cleared after sprite changes

**Why**: After regenerating `elias_sheet.png`, the game showed Elias as invisible or rendered the old sheet. Root cause: Godot's per-source-hash `.ctex` cache in `.godot/imported/` doesn't always re-import on a `--quit` boot. Symptom is silent — the game just shows stale pixels. Fix: run `Godot.exe --path <project> --headless --import` once after sprite writes.
**Affects**: `tests/run_smoke.py` workflow, this gotcha is now noted at the top of `projects/PaleGarden.md`.

## 2026-05-02 — SpriteCook MCP picked for follow-up Elias iteration

**Why**: Local LoRA + procedural animation is good but slow to iterate. SpriteCook's `generate_game_art` produces a canonical asset and `animate_game_art` produces consistent motion strips against the same `asset_id` — same shape as our hand-rolled pipeline but server-managed and higher fidelity. Skills `spritecook-{workflow-essentials,generate-sprites,animate-assets}` are installed globally. MCP server (`npx spritecook-mcp setup`) pending user setup; tools (`generate_game_art`, `animate_game_art`, `get_credit_balance`, `list_recent_assets`) are not yet available in-session.
**Alternatives considered**: Keep iterating on local LoRA + retrain with more reference data (slower, plateaus at the LoRA's rank-8 capacity). PixelLab API (similar but less integrated with Claude Code).
**Affects**: Once MCP is connected, `generate_elias_base.py` + `animate_elias_base.py` become legacy fallbacks and SpriteCook becomes the primary path. Still keep them since they don't depend on a paid service.
