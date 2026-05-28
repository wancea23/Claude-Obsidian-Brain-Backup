# Phase 3 — Days 4-6 Bruno & Old Journal

**Status:** ⏳ Pending · **Goal:** Bruno arrives Day 4 (let-in/shoo choice), bonds across Days 5-6 with day-specific behaviors. Old Journal discoverable Day 6 by tilling back-left corner. Rain Day 6.

## Prerequisites
- Phase 2 ✅ (farm tutorial loop works, day cycle solid)
- Bruno sprite exists at `assets/sprites/bruno.svg` ✅

## Steps

### 3.1 — Bruno arrival (Day 4)
- [ ] **3.1.1** Refactor `scenes/npcs/bruno.gd` to use new state machine: enum `{IDLE, FOLLOWING, SLEEPING, INVESTIGATING, FETCHING, CHASING_CROWS, WAITING_AT_GATE, OFFSCREEN}`. Replace existing `bruno_named`-as-presence logic with explicit `GameState.bruno_present` flag
- [ ] **3.1.2** Schedule arrival: on `day_started(4)` + 10s player-control timer → trigger `bruno_arrival()`
- [ ] **3.1.3** Bark via `AudioStreamPlayer2D` positioned at east-fence offscreen point. Use `AudioManager.play_sfx("dog_bark")`
- [ ] **3.1.4** When player approaches east fence (Area2D detection), spawn Bruno sprite outside gate, IDLE looking at player
- [ ] **3.1.5** Trigger DialogueBox choice via existing `show_choices` API: `[Let him in]` / `[Shoo him away]`
- [ ] **3.1.6** Let-in path: open existing `NamingPopup.tscn`. On `name_confirmed(text)` → set `bruno_present=true`, `bruno_named=(text != "")`, `bruno_name=text`. Empty text stored as `""` (Bible: Elias calls him "the dog" in journal). On submit, transition Bruno to INVESTIGATING state, visit 5 waypoints (each crop area, well, porch) → sit 2 tiles from Elias
- [ ] **3.1.7** Shoo path: Bruno visible through fence 30s timer → fade out → despawn. Set `bruno_present=false`

### 3.2 — Bruno day-by-day behaviors
- [ ] **3.2.1** Create `scripts/systems/bruno_behavior_scheduler.gd`. On `day_started`, set Bruno's daily behavior pattern. Skip everything if `not GameState.bruno_present`
- [ ] **3.2.2** Day 5: Bruno brings stick. Spawn stick sprite near Bruno. On Elias E-interact: throw stick (projectile arc), Bruno FETCHING (run, pickup, return). 4 throws then drops interest → IDLE
- [ ] **3.2.3** Day 5: add woodpecker ambient via `AudioManager.play_ambient("woodpecker", "AmbientBirds")` during AFTERNOON
- [ ] **3.2.4** Day 6 (rain — also in 3.6): Bruno sits on porch all day, refuses to enter farmhouse. Override FOLLOWING logic for this day
- [ ] **3.2.5** Day 5: Bruno investigates back-left corner once in afternoon (pathfinder waypoint), lies down facing away

### 3.3 — Bruno collar ambient
- [ ] **3.3.1** Add `AudioStreamPlayer2D` child of Bruno scene. Stream: `bruno_collar_loop.ogg` (file may not exist — handle gracefully). Volume -25dB, attenuation distance ~5 tiles, looping
- [ ] **3.3.2** Auto-mute on OFFSCREEN state (when shooed or in Act 3+ absent path)

### 3.4 — Bruno-absent parallel branch
- [ ] **3.4.1** Audit every Day 5-14 event that references Bruno: add `if not GameState.bruno_present: return` skip path. Touch: `BrunoBehaviorScheduler`, journal entries (already have `_bruno_absent` variants ✅), bread sniff sequence (Phase 5), tea cutscene Bruno-at-gate cue (Phase 4), crow chasing (Phase 5)
- [ ] **3.4.2** Smoke-test scenario: shoo Bruno Day 4, advance through Day 14, no null deref errors, no missing dialogue

### 3.5 — Old Journal discovery
- [ ] **3.5.1** Add Interactable area on Farm.tscn covering back-left corner tile. Text variants: `"day<6": "Overgrown. Looks like it hasn't been worked in years."`, `"flag:back_field_tilled": ""` (inert after dug)
- [ ] **3.5.2** Day 6+ tilling interaction triggers `_on_old_journal_discovery()`:
  - Override till animation with `till_stutter` SFX (`AudioManager.play_sfx("till_stutter")`)
  - Spawn OldJournal item sprite emerging from soil (Tween rise + opacity)
  - Single low piano note: `AudioManager.play_sfx("piano_sting")`
  - If `bruno_present`: `AudioManager.play_sfx("dog_throat")`
  - Instantiate `OldJournal.tscn` (already built ✅), add to UI overlay
- [ ] **3.5.3** Set `GameState.back_field_tilled = true` immediately. On UI close: `old_journal_pages_read` already tracked by UI ✅
- [ ] **3.5.4** Add Old Journal as permanent inventory item (cannot discard). Touch existing inventory UI

### 3.6 — Day 6 rain
- [ ] **3.6.1** Create `scenes/effects/rain.tscn` — GPUParticles2D rain streaks, shader applying outdoor desaturation ~15% + deeper greens
- [ ] **3.6.2** Activate on `day_started(6)` only. Add to Farm.tscn outdoor layer
- [ ] **3.6.3** `AudioManager.play_ambient("rain", "AmbientMisc")` when in farm scene, `play_ambient("rain_on_roof")` when in farmhouse. Reduce `robin` volume 50%
- [ ] **3.6.4** Crops auto-water on rain days (skip watering need). Add to `garden/garden.gd` day-rollover logic: if `day == 6`, mark all planted tiles as watered

## Files touched (expected)
- `scenes/npcs/bruno.gd` (state machine refactor)
- `scenes/npcs/Bruno.tscn` (add collar AudioStreamPlayer2D)
- `scripts/systems/bruno_behavior_scheduler.gd` (new)
- `scenes/world/Farm.tscn` (back-left interactable, Bruno spawn point)
- `scenes/effects/rain.tscn` (new)
- `scenes/garden/garden.gd` (rain auto-water)
- Possibly: `scenes/ui/inventory.tscn` (Old Journal permanent slot)

## Verification (smoke tests)
- [ ] Day 4: bark plays at 10s, walk to east fence → Bruno appears, choice works
- [ ] Name input: empty, normal, weird chars all save correctly
- [ ] Day 5 fetch: throws stick 4 times then Bruno stops
- [ ] Day 6: rain visible + audible, Bruno on porch (if present)
- [ ] Day 6: till back-left corner → Old Journal sequence fires, all 5 pages readable
- [ ] Bruno-absent full run Day 4 → Day 14: no crashes, journals use `_bruno_absent` text
- [ ] Bruno collar audible within 5 tiles, silent beyond

## Open questions
1. Bruno's collar `.ogg` — handle missing file with placeholder silence (current AudioManager behavior) or block on user composition?
2. Old Journal "permanent inventory" — does the existing inventory UI support non-discardable items? If not, scope creep into UI work
3. Rain shader — write a real shader or just use a CanvasModulate desaturation overlay?
