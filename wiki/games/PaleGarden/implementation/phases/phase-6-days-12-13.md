# Phase 6 — Days 12-13 Peak Polish

**Status:** ⏳ Pending · **Goal:** Days 12-13 should FEEL like peak. Visual warmth turned up, porch evening cutscene, quarter-note rest in music loop.

## Prerequisites
- Phases 2-5 ✅
- Audio file `farm_loop_jazz_piano_with_rest.ogg` composed (or accept silent placeholder)

## Steps

### 6.1 — Day 12 hot afternoon visual
- [ ] **6.1.1** In `scenes/world/time_of_day.gd`, add Day-12 override: if `GameState.current_day == 12 and TimeManager.current_phase == TimeManager.Phase.AFTERNOON`, override target color to `Color(1.0, 0.93, 0.78, 1.0)` (warmer amber) — only this day, this phase
- [ ] **6.1.2** Grass sway shader (if exists in `scenes/world/yard.gdshader` or similar): increase sway amplitude uniform from 0.5 → 1.0px for Day 12
- [ ] **6.1.3** No event, no dialogue — pure visual

### 6.2 — Day 13 porch evening scene
- [ ] **6.2.1** Add Interactable to porch chair in Farm.tscn. Text variants: `"day==13": "Sit."`, `"default": ""` (inert other days)
- [ ] **6.2.2** On Day 13 interact at GOLDEN_HOUR phase:
  - Disable player control
  - Elias sits animation (Tween position + sprite swap to sitting)
  - If `bruno_present`: Bruno sits beside (Tween position)
  - Camera pulls back slightly (Tween zoom out 5%)
  - 10s hold — player can stay longer
- [ ] **6.2.3** Stars appear: add `scenes/effects/Stars.tscn` particle system to north sky region. Visible only during this cutscene
- [ ] **6.2.4** Margaret's north window: Sprite2D at north edge with PointLight2D (warm `LAMP_GLOW` color). Visible from Day 13 NIGHT onward
- [ ] **6.2.5** Dismiss: any input → re-enable control. No penalty for skipping
- [ ] **6.2.6** Bible: this is the LAST clean evening before Act 2 — emotional weight is the point

### 6.3 — Quarter-note rest music variant
- [ ] **6.3.1** AudioManager already wired to swap to `farm_loop_jazz_piano_with_rest.ogg` on `day_started(12)` via `_swap_piano_to_rest_variant()` ✅
- [ ] **6.3.2** Verify swap works at runtime (silent if file absent)
- [ ] **6.3.3** No code changes if Phase 1 audio refactor is intact

## Files touched (expected)
- `scenes/world/time_of_day.gd` (Day 12 override)
- `scenes/world/Farm.tscn` (porch chair Interactable, Margaret window light)
- `scenes/cutscenes/PorchEvening.tscn` + `porch_evening.gd` (new — or inline in farm.gd)
- `scenes/effects/Stars.tscn` (new)

## Verification (smoke tests)
- [ ] Day 11 afternoon screenshot vs Day 12 afternoon screenshot: visibly warmer tint on Day 12
- [ ] Day 13 GOLDEN_HOUR: porch interaction available, cutscene plays
- [ ] Bruno sits beside chair if present
- [ ] Margaret window glow visible at NIGHT Day 13
- [ ] Music loop has audible pause before motif restart Days 12-14
- [ ] Day 13 night journal entry plays correctly ("I think I made the right decision")

## Open questions
1. Stars effect: particles or pre-rendered backdrop?
2. Camera pull-back: built into Camera2D zoom Tween or pre-scaled scene?
3. Porch chair sprite: needs sitting sprite variant for Elias?
