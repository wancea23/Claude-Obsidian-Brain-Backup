# PaleGarden — Todo

> Read [[projects/PaleGarden#Session bootstrap]] before picking up work here.

## Active — Yard Act 1 (2026-05-28)

- [ ] **Atlas mapping**: user to confirm Farm.png row/col mapping for `tomato` and `pumpkin` (turnip is row 3 cols [2,3,5,7,8]). Update `CROP_ATLAS` in `scenes/world/yard_zones.gd`.
- [ ] **Tall crops** (garlic row 13): wire `tall=true` + size_in_atlas (16×32) once user identifies which rows.
- [ ] **TileSet texture origins**: script a one-shot pass over yard.tscn's embedded `TileSetAtlasSource_yrlxp` (source id 3 of `TileSet_lwiud`) to set `texture_origin = Vector2i(8, 8)` on all crop atlas coords. User-painted cabbage etc. currently render single-tile because only row 9 cols 2-5 (cauliflower) has origins set.
- [ ] House door zone: Area2D on farmhouse door → [E] enters interior → bed advances DayManager.
- [ ] HUD overlay on Yard: day counter, gold, stamina, hunger.
- [ ] Day/Time wiring: DayManager + TimeManager not driving anything in new Yard. Hook SkyRect tint to phase, advance day from bed/rest action.
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
