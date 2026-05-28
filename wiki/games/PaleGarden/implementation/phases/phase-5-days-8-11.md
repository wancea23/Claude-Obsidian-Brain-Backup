# Phase 5 — Days 8-11 Disruption

**Status:** ⏳ Pending · **Goal:** Daily bread routine, two crow visit events (Day 9, Day 11), optional player-built scarecrow from 3 items (replaces existing rot-repair model).

## Prerequisites
- Phase 4 ✅ (Margaret fence + tea done; `margaret_helped` flag drives bread)
- Phase 3 ✅ (Bruno states for chasing crows)

## Steps

### 5.1 — Bread delivery system
- [ ] **5.1.1** Create `scripts/systems/bread_delivery.gd` autoload-eligible singleton OR scene-attached node. On `day_started(day)` where `day >= 8 and GameState.margaret_helped`: spawn bread sprite at farmhouse doorstep
- [ ] **5.1.2** Bread Interactable: `"Pick up bread"` → `AudioManager.play_sfx("cloth_unwrap")` → add to inventory as item OR consume immediately for `GameState.modify_stamina(+2)` (decide: real item vs effect-only)
- [ ] **5.1.3** Bruno follow override (if `bruno_present`): on bread pickup, transition Bruno to FOLLOWING state into farmhouse for one cycle, lie at Elias's feet
- [ ] **5.1.4** Skipped entirely if `margaret_helped=false` — no bread spawns

### 5.2 — Crow event system
- [ ] **5.2.1** Create `scripts/systems/crow_system.gd` + `scenes/effects/Crow.tscn`. Crow scene: AnimatedSprite2D (8×8, 2-frame peck animation), AudioStreamPlayer2D, simple AI
- [ ] **5.2.2** Crow sprite color: **dark amber sheen** (NOT blue-green from Bible — that violates palette). Use `Constants.PALETTE_ACT1.WOOD_AMBER` darkened
- [ ] **5.2.3** Day 9: on `day_started(9)`, spawn `Constants.CROW_COUNT_FIRST` (=5) crows at random crop tile positions. Use `AudioManager.play_sfx("crow_peck")` ambient
- [ ] **5.2.4** Day 11: spawn `Constants.CROW_COUNT_SECOND` (=9) crows — same mechanic, more aggressive
- [ ] **5.2.5** Shoo mechanic: when Elias position within `Constants.CROW_SHOO_RADIUS_TILES * Constants.TILE_SIZE` of a crow → all crows in radius scatter (wing-flap SFX `crow_scatter`, silhouettes circle 10s via Tween, despawn)
- [ ] **5.2.6** Affected CropPlots: each tile a crow was on → `yield_modifier -= Constants.CROW_YIELD_PENALTY` (=0.2), clamp min 0.5
- [ ] **5.2.7** First Day 11 shoo: show tooltip once via narrator dialogue `crow_tooltip_recurring` (already in npc_dialogue.json ✅)
- [ ] **5.2.8** Bruno (if present): on crow event, transition to CHASING_CROWS state — animated run-at-crows pattern, ineffective but committed

### 5.3 — Scarecrow build (player-initiated)
- [ ] **5.3.1** Add 3 Interactables to scenes (already partially built — Phase 1 Coat in Farmhouse ✅):
  - ShedPost: new Interactable in Farm.tscn SE corner. Text variants: `"default": "An old fence post."`, `"day>=11": "Could use this for something in the crop area."`, `"flag:has_scarecrow_post": ""` (inert)
  - CoatNail: already in `Farmhouse.tscn` ✅ — verify text variants correctly hook `has_scarecrow_coat`
  - StrawBundle: new Interactable in Farm.tscn near north fence. Text variants: `"default": "Dry straw. Not much use."`, `"day>=11": "Might be useful after all."`, `"flag:has_scarecrow_straw": ""` (inert)
- [ ] **5.3.2** On interact post-Day-11: set respective `has_scarecrow_*` flag true, despawn sprite. Use `GameState.set_flag()` API
- [ ] **5.3.3** Build trigger: when all 3 flags true, add Interactable to each empty crop plot area: `"Build scarecrow here?"`. On confirm:
  - 3-second AnimationPlayer sequence (post placement → coat hung → straw stuffed)
  - Spawn `scenes/effects/Scarecrow.tscn` (new — cheerful crooked figure sprite)
  - Set `GameState.scarecrow_rebuilt = true`. Clear the 3 has_ flags (consumed)
- [ ] **5.3.4** Update `crow_system.gd`: if `scarecrow_rebuilt`, crows approach crop edge, rotate to face scarecrow position, fly away (do NOT land, do NOT damage tiles)
- [ ] **5.3.5** Delete the existing `scarecrow_assembly.gd` + `ScarecrowAssembly.tscn` if scope-redundant after this implementation (it was a repair-model minigame, Bible spec is direct-place)

### 5.4 — Day 10 evening journal scene
- [ ] **5.4.1** On `day_started(10)`, when player triggers bed/journal at NIGHT: if `bruno_present`, set Bruno to special "head-on-foot" pose at Elias's chair position in farmhouse
- [ ] **5.4.2** Journal entry already in `journal_entries.json` ✅ ("The south field looks the way I imagined...")
- [ ] **5.4.3** After journal close: Bruno returns to default IDLE pose

### 5.5 — Day 11 Margaret ambient presence
- [ ] **5.5.1** Add `scenes/effects/MargaretLaundry.tscn` — line-of-laundry sprite at top of Farm.tscn, beyond north fence
- [ ] **5.5.2** On `day_started(11)` AFTERNOON phase: Tween in (2s fade-in) → hold 30s → Tween out (2s fade-out). One appearance per day
- [ ] **5.5.3** Increase chimney smoke particle intensity for the day (existing or new particle)
- [ ] **5.5.4** No interaction — texture only

## Files touched (expected)
- `scripts/systems/bread_delivery.gd` (new)
- `scripts/systems/crow_system.gd` (new)
- `scenes/effects/Crow.tscn` + `crow.gd` (new)
- `scenes/effects/Scarecrow.tscn` + `scarecrow.gd` (new)
- `scenes/effects/MargaretLaundry.tscn` (new)
- `scenes/world/Farm.tscn` (ShedPost, StrawBundle, doorstep interactables, laundry placement)
- `scenes/npcs/bruno.gd` (CHASING_CROWS state, bread-follow override)
- `scenes/garden/garden.gd` (yield_modifier per plot)
- Possibly delete: `scenes/minigames/scarecrow_assembly.gd`/`ScarecrowAssembly.tscn`

## Verification (smoke tests)
- [ ] Day 8 morning: bread on doorstep, eating gives +2 stamina (or whatever model)
- [ ] Day 8: if `margaret_helped=false`, NO bread spawns
- [ ] Day 9: 5 crows spawn, shoo within 3 tiles works, scatter visible
- [ ] Day 11: 9 crows, tooltip plays once on first shoo
- [ ] Collect all 3 scarecrow items post-Day-11 → build prompt appears on any empty plot
- [ ] Build → scarecrow visible, all subsequent crow spawns are deterred
- [ ] Day 10 night: Bruno head-on-foot pose visible (if present)
- [ ] Day 11 afternoon: laundry briefly visible
- [ ] Yield reduction confirmed on next harvest

## Open questions
1. Bread as inventory item vs immediate +2 stamina effect? (Affects UI)
2. Scarecrow sprite: simple ColorRect placeholder OR commission proper sprite now?
3. Delete `ScarecrowAssembly.tscn` (old repair-model) or repurpose as Phase 8 scaffolding?
4. Yield modifier needs persisting in save (per CropPlot) — extend save format?
