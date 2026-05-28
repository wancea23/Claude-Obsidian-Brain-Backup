---
project: The Pale Garden
engine: Godot 4.6 (GDScript only)
phase: Act 1 — Cozy farm sim foundation
last_updated: 2026-05-05
---

# The Pale Garden — Project Overview

A 4–5 hour pixel-art farm-sim that turns into a horror game. Act 1 (Days 1–14) is genuinely warm and pastoral; Acts 2–5 break that.

## Current state

**Built in this session (2026-04-30):**
- Walkable top-down farm map (640×640 world, viewport 640×360, scrollable)
- Player character (Elias) — placeholder rectangle with walk-bob animation, WASD movement, facing direction
- Painted world: forest borders with 30 deterministic tree silhouettes, grass clearing, dirt fields, garden plots
- Farmhouse placeholder with roof, walls, windows, door, chimney+smoke, fence around grass
- Decorative props: well, mailbox, scarecrow, flower tufts, path stones
- Three garden plot clusters (left/center/right) covered by one wide GardenZone Area2D
- Three interaction zones with `[E]` prompt: garden / house door / market gate
- Garden interaction redesigned: walk close → `[E] Tend the Garden` → modal menu with 4 tool cards (TILL / WATER / PLANT / HARVEST)
- Stamina system (6 dots in HUD, restored on sleep, paces actions per day)
- Time-of-day visual cycle (morning amber → noon clear → evening orange → night dark blue, advances every 3 actions)
- Crop variety (turnip / tomato / pumpkin) with type-coloured fruit placeholder and per-type harvest gold
- Crop visual `_draw()` placeholder showing seed → sprout → bloom → ripe-fruit-with-sparkle → wilt
- Inventory display in HUD (`T:N M:N P:N`)
- Tutorial dialogue auto-triggers on Day 1 first farm load
- House → `[E] Rest / Journal`, market gate → `[E] Travel to Market` (only on Days 7/14)
- Bruno (dog) auto-spawns from Day 4 onward as ambient NPC; Margaret + Seller are event-driven only
- Camera follows Elias with smooth limits at map edges; farmhouse blocks movement
- NPC `_draw()` silhouette placeholders (since no real sprites yet) with subtle ambient breathing scale animation

## Active focus
Cozy-loop completion: plant → wait → water → harvest → sell at market on Day 7. The loop now closes end-to-end.

## Tech stack
- Godot 4.6, GDScript with full static typing
- All visuals are placeholder coloured rectangles (`_draw()`) — no real pixel-art sprites yet
- Per-day action economy via stamina; per-day visual progression via WarmOverlay tween
- DialogueManager / DayManager / GameState / AudioManager autoloads drive cross-scene state
- Content-driven (events.json, npc_dialogue.json, journal_entries.json)

## Sprite pipeline (added 2026-05-05)
- Elias now uses **Universal LPC Character Generator** sheets (`assets/sprites/Elias/elias_v1.png`, 832×3456, 64×64 frames)
- **Walk animations**: rows 8–11 (0-indexed), 9 frames/direction, N/W/S/E order
- **Idle animations**: rows 22–25 (0-indexed), 2 frames/direction, directional (faces last walked direction)
- `elias.gd` tracks `_facing` to show correct directional idle when stationary
- `V1_SCALE = 0.75` scales 64px frames to ~48px on screen
- Convention for ALL future characters: LPC rows N=0, W=1, S=2, E=3 per animation group

## What it does NOT have yet
- NPC sprites (Margaret, Bruno, The Seller still use `_draw()` placeholders)
- Forest/house/crop sprites (still colored rects)
- Any audio (AudioManager guards against missing files; no music/SFX bundled)
- Working market scene (logic exists, visuals empty)
- Plant entity (Act 2 — the blood plant)
- Demon roster / horror systems (Acts 3+)
- Sleep cutscene (currently goes through Journal modal)
