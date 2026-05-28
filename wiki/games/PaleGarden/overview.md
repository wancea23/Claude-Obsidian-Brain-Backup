# The Pale Garden — Vault Overview

**Phase**: Act 1 development (Days 1-14, cozy farm, zero horror)
**Engine**: Godot 4.6 / GDScript
**Last updated**: 2026-05-27

## Current state
- Complete game scaffold: 54+ GDScript files, all scenes
- Garden system: 8×6 tile grid, crop lifecycle (5 phases), stamina 5/day
- Full garden overlay UI (E key → full-screen interface)
- Seed picker UI, day transition (journal entry on sleep)
- NPC scaffold: Elias, Margaret, Bruno, The Seller
- Events system: 14-day event triggers in events.json
- Save system: user://save.cfg via ConfigFile

## Toolchain (mandatory for all sessions)
- **Godot MCP**: `@satelliteoflove/godot-mcp` in `Code/.mcp.json`, WebSocket port 6550. Godot must be open with plugin enabled. Prefer MCP tools over raw `.tscn` edits.
- **Skills**: `godot-ui` (Control nodes, themes, layouts) + `godot-gdscript-patterns` (signals, state machines, optimization) at `~/.agents/skills/`. Read before writing code.
- **Agents**: 10 roles at `Games/.claude/agents/gamedev/` — director, architect, coder, narrative-writer, game-designer, artist, audio-engineer, ui-agent, tester, reviewer. File-mediated coordination.
- **Child CLAUDE.md loading**: `Code/CLAUDE.md` instructs Claude to read `Games/CLAUDE.md` when working under `Games/`. Not auto-loaded — instruction-based.

## Architecture decisions
- Day-driven (not wall-clock): crops advance on DayManager.day_ended signal
- CanvasLayer layers: HUD=5, GardenOverlay=10, DialogueBox=10, DayTransition=15
- Save: ConfigFile at user://save.cfg
- All strings from content/*.json — never hardcoded in .gd

## What needs work
- Sprites: SVG pixel-art placeholders exist, SD 1.5 run needed for PNG
- Audio: placeholder only, no real audio files yet
- Bruno AI: follow behavior needs implementation
- Hunger: tracked in GameState, visual feedback being added
- Market bartering: scaffold exists, full minigame needed

## Links
- [[mechanics/garden-grid]]
- [[mechanics/crop-lifecycle]]
- [[mechanics/stamina-economy]]
- [[mechanics/hunger-system]]
- [[mechanics/bruno-ai]]
- [[mechanics/npc-trust]]
- [[narrative/storyline-graph]]
- [[implementation/act1-build-plan]] — Godot build plan (7 phases) + gaps analysis
- [[implementation/phases/index]] — step-by-step build pages, user-driven
