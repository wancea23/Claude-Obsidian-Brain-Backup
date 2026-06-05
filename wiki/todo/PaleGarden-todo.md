# PaleGarden — Todo

> Read [[projects/PaleGarden#Session bootstrap]] before picking up work here.

## Active — Yard depth sorting / fence occlusion (2026-05-30) — RESUME HERE

> **Full state + open-issue checklist + 3 hypotheses + the real fix:**
> [[../games/PaleGarden/implementation/yard-depth-sorting]]. Read it first.

- [ ] **OPEN: horizontal SOUTH fences don't occlude the player** (esp. the
  barn-yard bottom rail's leftmost tiles — Elias draws *over* them; collision is
  fine). Everything else works (roof occlusion ✓, vertical fences ✓, under-roof
  collision ✓, most horizontal fences ✓). **Next session, in a fresh chat with
  MCP reconnected + project copied off OneDrive:**
  1. `mcp__godot__godot_editor get_state` → confirm bridge live.
  2. Run, drive Elias to the barn-yard bottom rail (left end), screenshot.
  3. Likely cause: **stale code (OneDrive)** and/or **`set_layer_y_sort_origin`
     not applying to the legacy `Fence` TileMap** (fence then sorts from its top,
     player draws over it). See canonical page §"open issue".
  4. **Real fix (removes all tuning):** convert legacy `TileMap`s — **Magazie,
     Fence, Vegetation** — to `TileMapLayer`s so everything sorts per-tile at its
     base; then drop the player-flip + `occlude_*` knobs.
  5. **FIRST: revert the dead-end `yard.tscn` edits from 2026-05-30 (later)** —
     `y_sort_enabled=true` on `Yard`/`Fence`/`BarnFence` (+ layers) and `z_index=5`
     on `Vegetation`/`BarnBody`/`BarnRoof`/`BarnDoor` were added directly to the
     scene; they're **redundant with `yard_loop.gd` and overridden at runtime** (no
     effect). Depth is script-only — remove them so the scene matches the design.
     (Cosmetic leftover to keep/ignore: barn-yard bottom rail trimmed to `x5–14`,
     the `x4,y23` stub removed.) See [[../games/PaleGarden/implementation/yard-depth-sorting]] "Update 2026-05-30 (later)".
- [x] ~~Roof occlusion (all buildings)~~ ✓ confirmed. ~~Vertical fences solid~~ ✓.
  ~~Walk under Magazie roof~~ ✓ (`roofed_building_paths`). All in
  `yard_loop.gd` + `yard_collisions.gd`, runtime-only.

> **BLOCKERS this session (why it's unfinished):** (1) Godot MCP died — BLACKBOX
> grabbed the connection, mine wouldn't reconnect → couldn't drive/screenshot.
> (2) OneDrive → Godot served stale code on reload → fixes may not have run.
> Fix both before resuming: close BLACKBOX, fresh Claude session (reconnects MCP),
> copy project to `C:\Games\PaleGarden`.

- [ ] **Manual verify the day advance**: in the editor, walk to the house front (or click HUD **Rest**) → Sleep in the diary → confirm `DayTransition` plays, HUD flips to Day 2, and the tint resets to dawn. The logic is a `farm.gd` port and boots clean, but wasn't screenshotted (E/clicks aren't MCP-injectable). See [[../games/PaleGarden/implementation/phases/phase-2-days-1-3#Yard day loop — completed 2026-05-29]].
- [x] ~~**HUD tool buttons on yard**~~ — **done 2026-05-29**: hidden on the yard. Added `hide_tools()`/`show_tools()` to `scenes/ui/hud.gd` (hides the `$TopBar/Tools` HBoxContainer); `yard_loop.gd::_build_hud()` calls `_hud.hide_tools()`. Planting/tending stays on the garden overlay.
- [x] ~~**Stale `yard_tool.gd`**~~ — **done 2026-05-29**: neutered the runtime rebuild. The script is attached to the **Yard root** (not `YardLoop`, which holds `yard_loop.gd`); its only live target layers `Structures`/`Objects` are `visible = false` leftovers from the pre-handpaint era. `_ready()` no longer calls `_rebuild()` (now `pass` + LEGACY banner), killing the `Ground TileMapLayer not found` boot warning and the per-launch clear/repaint of two hidden layers. Inspector `rebuild_layout` toggle still works for manual editor use. Optional future cleanup: fully detach the script from the Yard root in `yard.tscn`.
- [ ] **House interior (optional)**: rest currently opens the diary in place; there's no separate interior scene. Build one only if the design wants an interior beat.

## Active — Yard Act 1 (2026-05-28)

- [ ] **Atlas mapping**: user to confirm Farm.png row/col mapping for `tomato` and `pumpkin` (turnip is row 3 cols [2,3,5,7,8]). Update `CROP_ATLAS` in `scenes/world/yard_zones.gd`.
- [ ] **Tall crops** (garlic row 13): wire `tall=true` + size_in_atlas (16×32) once user identifies which rows.
- [ ] **TileSet texture origins**: script a one-shot pass over yard.tscn's embedded `TileSetAtlasSource_yrlxp` (source id 3 of `TileSet_lwiud`) to set `texture_origin = Vector2i(8, 8)` on all crop atlas coords. User-painted cabbage etc. currently render single-tile because only row 9 cols 2-5 (cauliflower) has origins set.
- [x] ~~House door zone~~ — **done 2026-05-29** as a full-width frontage rest zone (door art is decorative/undetectable). No interior transition.
- [x] ~~HUD overlay on Yard~~ — **done 2026-05-29**.
- [x] ~~Day/Time wiring~~ — **done 2026-05-29**: `time_of_day.gd` tints by `TimeManager` phase; rest/sleep advances the day via `DayManager.advance_day`.
- [ ] Garden patch crops: only renders inside the overlay's `CropContainer` AND on yard via `yard_zones._spawn_or_update_crop`. Verify no double-render after overlay closes.

## Stale — old Farm.tscn scene (kept for reference, not the main scene)

Original sprite-pipeline / SpriteCook items below are paused — main scene is now `scenes/world/yard.tscn`, not `Farm.tscn`. Elias sprites already render in-game.

- [ ] **User**: run `npx spritecook-mcp setup` in a terminal, then say
  "MCP ready" in chat. Don't paste the API key into chat — the setup CLI
  handles auth. After this, `/mcp` should list `spritecook` as connected.

## Next session (blocked on the active item above)

- [ ] Call `get_credit_balance` to confirm there's enough budget.
- [ ] Generate ONE canonical Elias still with `generate_game_art`. Prompt
  template: `eliaspx pixel art character, young man front view standing
  still, brown swept hair, green shirt, dark navy pants, brown boots,
  transparent background, sharp pixels`. `width=64`, `height=96`,
  `pixel=true`, `bg_mode="transparent"`, `smart_crop_mode="tightest"`,
  `model="gemini-3.1-flash-image-preview"`. Save the returned `asset_id`
  to a new `PaleGarden/spritecook-assets.json` manifest.
- [ ] Animate that `asset_id` 5×: `Idle`, `Walk down`, `Walk up`,
  `Walk left`, `Walk right`. `auto_enhance_prompt=true`, `output_format="spritesheet"`,
  `output_frames=8`, `pixel=true`. Download each `sprite_url` to
  `PaleGarden/assets/sprites/elias_*_strip.png`.
- [ ] Rebuild `elias_sheet.png` + `elias_sheet.json` from the new strips
  (reuse `animate_elias_base.py`'s sheet-assembly path or write a small
  one-off — strips already in correct order).
- [ ] Run `Godot.exe --headless --import` once, then `tests/run_smoke.py`,
  attach screenshots to a new entry in [[chat-history/PaleGarden-chats]].
- [ ] Update [[projects/PaleGarden#Session bootstrap]] to flip the
  pipeline status from "pending SpriteCook setup" to "SpriteCook live".

## Parking lot — Act 2 (Days 15–25)

Untouched this week. Lives in [[games/PaleGarden/narrative/storyline-graph]].

- [ ] `TheEntity.tscn` + script
- [ ] Whisper floating text system
- [ ] Day 20 tendril event
- [ ] Day 22 JS-02 (the seller's eyes)
- [ ] Day 25 bloodletting minigame

## Bootstrap (one-time per machine)

- [ ] System Python deps already on this machine (see bootstrap section in
  project page). For a fresh machine: `python -m venv ~/gamedev-tools-venv
  && ~/gamedev-tools-venv/Scripts/pip install -r
  Code/Games/gamedev-tools/requirements.txt` (~10–20 min, ~5 GB).
- [ ] Godot 4.6 binary at
  `C:/Users/johns/Downloads/Godot/Godot_v4.6.2-stable_win64.exe`. Not on
  PATH — invoke by full path. (If you want it on PATH: `setx PATH
  "%PATH%;C:\Users\johns\Downloads\Godot"` then restart the terminal.)
- [ ] Trained LoRA at `gamedev-tools/loras/elias_palegarden/` is
  per-machine + gitignored. Retrain on a fresh machine via
  `gamedev-tools/lora_training/{prepare_dataset,train_lora}.py`.

## Done this session (2026-05-02) — for context

See [[chat-history/PaleGarden-chats]] for the full log.

- LoRA trained on the Elias reference sheet (rank 8, 1500 steps).
- Slicer rewritten with two-color bg keying + foot-anchor alignment.
- AnimateDiff back-view attempt failed; replaced with deterministic
  recolor (`make_walk_up_from_walk_down.py`).
- Final pipeline: `generate_elias_base.py` (AI bases) +
  `animate_elias_base.py` (procedural limb shifts).
- Pixel-stability verified via `ImageChops.difference` — frame 0 vs 3
  byte-identical, other frames diff only in y≥14.
- Smoke tested in-game; screenshots in `PaleGarden/tests/shots/`.
