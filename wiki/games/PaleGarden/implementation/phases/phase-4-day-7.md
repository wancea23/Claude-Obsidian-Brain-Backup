# Phase 4 — Day 7 Market & Margaret

**Status:** ⏳ Pending · **Goal:** Migrate Margaret encounter from Day 10 to Day 7 (already in events.json ✅). Refresh fence-repair minigame. Add tea cutscene with the "we" pause. First crow ambient at evening.

## Prerequisites
- Phase 3 ✅
- Bruno-absent branch tested (Margaret encounter must work without Bruno)

## Steps

### 4.1 — South gate opens on market days
- [ ] **4.1.1** In `scenes/world/farm.gd`, on `day_started(7)` and `day_started(14)`, enable south gate transition zone (was disabled previous days) and swap gate sprite to open
- [ ] **4.1.2** Add ambient `AudioStreamPlayer2D` at south edge playing `market_chatter` at low volume (distance attenuation creates "far away" feel)
- [ ] **4.1.3** First-approach tooltip via existing prompt system: `"Market today. The gate is open."`

### 4.2 — Market scene refresh
- [ ] **4.2.1** Open `scenes/world/Market.tscn`. Verify all 5 stalls present: Produce, Seed, Tool, Margaret, Seller. If Seller stall not built, add it (will be empty until Day 14)
- [ ] **4.2.2** On `_ready()` of Market scene, check `GameState.current_day`. If < 14, Seller stall hidden + collision disabled
- [ ] **4.2.3** Margaret stall: produce + preserves sprites, Margaret NPC behind. Use existing Margaret.tscn (placeholder _draw OK for now)
- [ ] **4.2.4** Trigger `AudioManager.play_market_theme()` on Market scene `_ready()`. Stop on exit
- [ ] **4.2.5** Add market ambient: `AudioManager.play_ambient("market_chatter", "AmbientMisc")`

### 4.3 — Margaret encounter (Day 7)
- [ ] **4.3.1** Refactor `scenes/npcs/margaret.gd`. Replace `@export interaction_state` per-scene-instance logic with day-driven: in `_ready()`, if Day 7 and `not margaret_helped` → set proactive trigger
- [ ] **4.3.2** Proactive trigger: when player enters market scene on Day 7, after 2s `await`, start dialogue (player doesn't click first — Margaret flags Elias down per Bible)
- [ ] **4.3.3** Dialogue flow: `DialogueManager.start_dialogue("margaret", "greeting_day7")` (already in JSON ✅) → on finish → `"fence_intro_day7"` → show choice `[I'll take a look]` / `[I'm a bit stretched today]`
- [ ] **4.3.4** Accept choice: transition to fence repair minigame. Decline: `npc_dialogue.fence_intro_decline` line, set `margaret_helped=false`, NO trust penalty (Bible: she just nods)

### 4.4 — Fence repair minigame refresh
- [ ] **4.4.1** Audit existing `scenes/minigames/FenceRepair.tscn` + `fence_repair.gd`. Confirm 5 planks, drag-and-drop, snap-to-slot. If structure differs from Bible spec, refactor
- [ ] **4.4.2** Interleave Margaret's lines during play. Use `DialogueManager.start_dialogue("margaret", "fence_repair_chat")` (multi-line array, already in JSON ✅). Lines should appear in a non-blocking text panel — player keeps playing
- [ ] **4.4.3** Completion: `plank_snap` SFX on each placement, on all-5-complete: `npc_dialogue.margaret.fence_fixed` plays, set `margaret_helped=true`, `npc_trust.margaret += 20` (existing API: `set_npc_trust("margaret", 20)`), `GameState.modify_conscience(+1)`

### 4.5 — Tea cutscene
- [ ] **4.5.1** Create `scenes/cutscenes/MargaretTea.tscn` + script. Simple scene: porch background ColorRect, two character sprites seated, dialogue box overlay
- [ ] **4.5.2** `EventBus.player_control_enabled.emit(false)` equivalent — disable player input (no EventBus exists; emit signal on `GameState` or check existing `main.gd` for control gating)
- [ ] **4.5.3** Play `npc_dialogue.margaret.tea_scene` lines (array of 5, already in JSON ✅). Line 4 is `"We planted sunflowers along the north fence every summer."`
- [ ] **4.5.4** **Implement the "we" pause**: before showing line 4, `await get_tree().create_timer(0.0).timeout`; before showing line 5 (`"...Anyway. More tea?"`) the dialogue box should hold the previous line ~0.8s longer than usual. Custom delay parameter or one-frame Margaret sprite shift
- [ ] **4.5.5** On finish: queue_free cutscene, re-enable control, return to market scene

### 4.6 — First crow call ambient
- [ ] **4.6.1** On `day_started(7)` GOLDEN_HOUR phase transition (subscribe `TimeManager.phase_changed`), play `AudioManager.play_ambient("crow_distant", "AmbientBirds", looping=false)` once
- [ ] **4.6.2** Player just registers a new sound. No tooltip, no marker. Pure atmospheric setup for Day 9

## Files touched (expected)
- `scenes/world/farm.gd` (gate open logic, market chatter)
- `scenes/world/Market.tscn` + `market.gd` (Seller hide logic, market theme)
- `scenes/npcs/margaret.gd` (Day 7 proactive trigger refactor)
- `scenes/minigames/fence_repair.gd` (chat interleave + completion flags)
- `scenes/cutscenes/MargaretTea.tscn` + `margaret_tea.gd` (new)
- `globals/GameState.gd` (control-enable signal if not already present)

## Verification (smoke tests)
- [ ] Day 7 morning: south gate opens, tooltip shows
- [ ] Walk through gate → Market loads, Seller absent, market theme plays
- [ ] Approach Margaret → she initiates dialogue without click
- [ ] Accept fence → minigame fires, Margaret talks during, completes cleanly
- [ ] Tea cutscene plays with audible 0.8s pause after "we", facial shift visible
- [ ] After tea, control returns, market still browsable
- [ ] GOLDEN_HOUR: single crow call audible
- [ ] `margaret_helped=true`, trust +20, conscience +1 — confirm in save file
- [ ] Bruno-absent run: tea cutscene skips Bruno-at-gate beats cleanly

## Open questions
1. Tea cutscene visuals: full scene with character sprites OR static illustration card? (Asset budget)
2. Margaret's facial shift on "we" pause: one-frame sprite swap, or just hold dialogue silence? (Asset cost vs effect)
3. Existing fence_repair minigame: full audit needed — may or may not match Bible's 5-plank spec
