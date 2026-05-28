# PaleGarden

> 2D pixel-horror garden simulator. First game in `Code/Games/`. Built with Godot 4.6 + GDScript by a 10-agent gamedev team.
> **Phase**: Act 1 complete (Days 1–14, cozy farm loop, zero horror) · **Last updated**: 2026-05-02

## Session bootstrap

If you've just opened a chat in this project, read **only this section** plus
[[decisions/PaleGarden-decisions]] and [[todo/PaleGarden-todo]]. Don't grep
the source tree — the vault knows what's there.

**Today the project is**: Act 1 playable. Sprite pipeline for Elias was
rewritten end-to-end this week; current Elias renders in-game with
pixel-stable walk cycles.

**Last working session**: 2026-05-02 — sprite-pipeline rewrite. See
[[chat-history/PaleGarden-chats]] for the chronological log.

**Pipeline status**:
- **Elias sprites**: ✅ in-game and pixel-stable. Pending: SpriteCook MCP
  iteration (user must run `npx spritecook-mcp setup` first).
- **Audio**: untouched this week.
- **Act 2**: untouched (parking lot — see todo).

**Active work**: see top of [[todo/PaleGarden-todo]] — blocked on user
running `npx spritecook-mcp setup`.

**Sprite-pipeline files** (don't re-discover them):

| Path | Role |
|------|------|
| `gamedev-tools/generate_elias_base.py` | SD 1.5 + eliaspx LoRA → 3 canonical 32×48 bases (front/back/side). Run once, output frozen. |
| `gamedev-tools/animate_elias_base.py` | Pure Pillow. Loads bases, builds strips by `out = base.copy(); shift(legs); shift(arms)`. Pixel-stable head/torso. |
| `gamedev-tools/loras/elias_palegarden/` | Trained DreamBooth-LoRA, rank 8, fp16. Gitignored, ~6.4 MB. |
| `gamedev-tools/lora_training/{prepare_dataset,train_lora}.py` | Recipe to retrain the LoRA from `source/elias_reference.png`. |
| `gamedev-tools/lora_training/source/elias_base_{front,back,side}.png` | Frozen AI bases. Replace these to change the look. |
| `gamedev-tools/slice_elias_reference.py` | Older path: slice the 5×6 reference sheet directly. Kept for any future hand-aligned reference. |
| `gamedev-tools/make_walk_up_from_walk_down.py` | Helper: derive a back-view strip by recoloring head pixels to hair color. |
| `PaleGarden/assets/sprites/elias_*_strip.png` + `elias_sheet.png` + `.json` | Game-side artifacts that `elias.gd` consumes. |
| `PaleGarden/scenes/world/elias.gd` | Consumer. 32×48 frames, 5 anim rows: idle / walk_down / walk_up / walk_left / walk_right. |
| `PaleGarden/tests/run_smoke.py` | Auto-launches Godot, clicks New Game, drives WASD, screenshots `tests/shots/`. |

**Re-import gotcha**: after sprites change on disk, run
`Godot.exe --headless --import` once before `run_smoke.py`. Otherwise Godot
serves the stale `.ctex` from `.godot/imported/` and the character either
disappears or shows old frames.

**Spritecook skills installed** (see [[skills-installed]]):
`spritecook-workflow-essentials`, `spritecook-generate-sprites`,
`spritecook-animate-assets`. They expect MCP tools that aren't connected
yet — user runs `npx spritecook-mcp setup` to wire them in.

**System Python deps already installed** (so I don't reinstall):
`torch+cu118`, `diffusers 0.38.0`, `peft`, `accelerate`, `transformers`,
`safetensors`, `mss`, `pyautogui`, `pywin32`, Pillow.

**Godot binary on this machine**:
`C:/Users/johns/Downloads/Godot/Godot_v4.6.2-stable_win64.exe`
(not on PATH — invoke by full path).

## What it is

A farmer tends a garden that turns out to be aware. Plants whisper, soil remembers, and what grows asks for things back. Five endings, non-linear (The Devoted / The Gardener's Peace / The Harvest / The Rot / The Witness).

## Stack

- **Engine**: Godot 4.6 (GDScript only, no C#)
- **Resolution**: 640×360 (16:9, 3× scale)
- **Tile / sprite size**: 32 px
- **Asset gen**: SD 1.5 + pixel-art LoRA via `Code/Games/gamedev-tools/artist_agent.py` (requires CUDA venv)
- **Audio gen**: AudioCraft (MusicGen + AudioGen) via `Code/Games/gamedev-tools/audio_agent.py`
- **ML venv**: `C:/Users/johns/gamedev-tools-venv/` (per-machine, bootstrap from requirements.txt)

## Current state (2026-05-02)

**Act 1 fully playable** (unchanged from 2026-05-01) — garden overlay, seed
picker, stamina+hunger, crop lifecycle, NPC dialogue, Days 1–14 events,
Bruno AI, full storyline DAG in vault.

**Sprite pipeline rebuilt this week**: replaced the original SVG-based
Elias with an AI-generated + procedurally-animated set. New strips are
in-game and pixel-stable (frame-0 vs frame-3 byte-identical, other frame
diffs confined to leg/arm band). See bootstrap above for the file map.

**Open**: SpriteCook MCP integration (skills installed, MCP server
pending user setup), Act 2 (untouched).

## Key files

| File | Role |
|------|------|
| `STYLE.md` | Palette, audio tone, sprite prompt formula |
| `globals/Constants.gd` | All constants — palette, tile size, stamina, hunger, crop phases |
| `globals/GameState.gd` | All flags: `bruno_named`, `margaret_helped`, `seed_obtained`, HUNGER, CONSCIENCE |
| `globals/DayManager.gd` | Day advance + event dispatch; hunger wasting cap |
| `scenes/garden/garden.gd` | Tile state manager, public API, signals |
| `scenes/ui/GardenOverlay.tscn` | Full-screen garden interface (E to open) |
| `scenes/ui/SeedPicker.tscn` | Crop type selector popup |
| `scenes/world/farm.gd` | All 14-day event handlers, overlay wiring |
| `scenes/npcs/bruno.gd` | Follow AI + north-field avoidance |
| `content/events.json` | Day 1–14 event triggers (18 event IDs) |
| `content/npc_dialogue.json` | Narrator, Margaret, The Seller dialogue |
| `content/journal_entries.json` | Elias's 14-day diary |
| `asset_requests.json` | 27 sprite requests, all fulfilled |
| `audio_requests.json` | Pending audio gen requests |
| `review.md` / `bugs.md` | Cross-agent coordination logs |

## Detailed vault

Per-game vault lives at `graphify-out/wiki/games/PaleGarden/`:
- [[games/PaleGarden/overview]] — pitch + current phase
- [[games/PaleGarden/decisions]] — design log
- [[games/PaleGarden/chat-history]] — session-by-session
- [[games/PaleGarden/narrative/storyline-graph]] — non-linear DAG (4 endings)
- `mechanics/` — one .md per system (filled by Game Designer)
- `narrative/{events,characters,endings}/` — per-page lore (filled by Narrative Writer)

Note: this project page is the global index entry. The per-game vault is the
operational source of truth the agents read/write.

## Notes & gotchas

- **Subagents in Claude Code can't talk directly** — only Director spawns them
  via the Task tool. All cross-agent communication is **file-mediated**
  (asset_requests.json, audio_requests.json, vault pages, review.md).
  The diagram lines = data flow, not conversations.
- **OneDrive caveat**: heavy ML venv lives at `~/gamedev-tools-venv/` (per-machine,
  bootstrapped from `gamedev-tools/requirements.txt`). Never put 5 GB of torch
  wheels inside OneDrive.
- **Godot 4 vs 3 syntax**: agents are wired to Godot 4.3 only. Reviewer flags
  any 3.x syntax (`onready var`, `export var`, `yield`, old `connect()`,
  `Vector2()` for zero) as `[GD3]`.
- **VRAM (8 GB)**: audio_agent.py runs MusicGen first, unloads, then AudioGen.
  artist_agent.py defaults to batch=4 — drop to 2 if OOM.
- **Tester pyautogui safety**: don't run windowed tests while you're using the
  same keyboard/mouse — clicks land wherever the cursor is.
