# The Pale Garden — Decisions

> Owned by Game Designer. Every design decision logged here. Append-only.

Format:
```
## YYYY-MM-DD — <decision title>
**Why**: <one sentence motivation>
**Alternatives considered**: <what else was on the table and why rejected>
**Affects**: [[mechanics/X]], [[narrative/endings/Y]]
```

---

## 2026-05-27 — Godot MCP + skills + agents as mandatory toolchain

**Why**: Direct `.tscn` file editing desynchronizes the Godot editor. The Godot MCP plugin (`@satelliteoflove/godot-mcp`) bridges Claude Code to the running editor via WebSocket on port 6550, keeping scenes in sync. Two skills (`godot-ui`, `godot-gdscript-patterns`) provide pattern reference. The 10 gamedev agents handle multi-role work. All three layers are now mandatory for Pale Garden sessions.
**Setup**:
- MCP registered in `Code/.mcp.json` → `npx -y @satelliteoflove/godot-mcp`
- Godot editor must be open with "Godot MCP" plugin enabled (Project Settings → Plugins)
- `Games/CLAUDE.md` has the rules: run `ToolSearch("mcp__godot")` at session start, prefer MCP over raw edits, read skill files before writing GDScript/UI
- `Code/CLAUDE.md` has a child-project import: "when working under Games/, read Games/CLAUDE.md first"
- Memory file `feedback_godot_tooling.md` reinforces the same rules
**Limitation**: Claude Code doesn't auto-load child CLAUDE.md files. The import rule in root CLAUDE.md is an instruction Claude follows (reads the file), not system-enforced auto-loading. Works reliably because both CLAUDE.md instruction + memory file remind Claude.
**Affects**: all Pale Garden development sessions, `Code/CLAUDE.md`, `Games/CLAUDE.md`, `Code/.mcp.json`

## 2026-04-30 — Day-driven crop growth, not wall-clock timers

**Why**: Crops advancing on `DayManager.day_ended` signal keeps growth deterministic and design-legible — "this crop needs 3 days of water" rather than "this crop needs 72 real seconds."
**Alternatives considered**: Timer nodes per crop (simpler but would decouple from day system, causing crops to grow while player reads journal).
**Affects**: [[mechanics/plant-state-machine]], [[mechanics/garden-grid]]

## 2026-04-30 — CanvasLayer-per-scene architecture (no shared UILayer)

**Why**: Each CanvasLayer-rooted scene (HUD layer=5, DialogueBox layer=10, DayTransition layer=15) manages its own z-order. A shared UILayer caused Control children to render outside screen coordinates.
**Alternatives considered**: Single UILayer CanvasLayer holding all UI (simpler but broke Control anchoring for overlays). Final solution: CanvasLayer scenes added to Farm node directly; a `_ui_canvas` (layer=8) created in code holds Control-rooted minigame overlays.
**Affects**: `scenes/world/farm.gd`, `scenes/world/market.gd`, all UI scenes

## 2026-04-30 — Planting minigame: retry on wrong tile, no penalty mid-session

**Why**: Emitting failure signal mid-session then resetting caused double-emit issues (farm.gd received both a fail and a success result). Cleaner: wrong tile flashes red and resets highlights, player retries same sequence, signal fires exactly once on success or when player exits.
**Alternatives considered**: Single-attempt (one wrong tap = instant fail + close). Rejected because the minigame is introduced Day 1 as tutorial — too punishing.
**Affects**: `scenes/minigames/planting_minigame.gd`

## 2026-04-30 — `class_name Garden` for typed access from farm.gd

**Why**: `_garden` typed as `Node2D` caused GDScript warnings when accessing Garden-specific properties (`active_tool`, `planting_minigame_requested`). Adding `class_name Garden` allows `_garden: Garden` typing with full type safety.
**Alternatives considered**: Type as `Node` and use `get("active_tool")` duck typing (works but loses type checking); cast with `as` on every access (verbose).
**Affects**: `scenes/garden/garden.gd`, `scenes/world/farm.gd`

## 2026-04-29 — Four endings, not three

**Why**: A hidden fourth ending ([[narrative/endings/unmarked]]) gives players who notice the garden's pattern early a reason for a second playthrough. Three endings felt too symmetric.
**Alternatives considered**: Three endings (cleaner but less replayable); branching hidden state inside one ending (technically simpler but less satisfying).
**Affects**: [[narrative/storyline-graph]], all four [[narrative/endings/]]
