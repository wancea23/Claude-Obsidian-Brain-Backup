# Phase 7 — Day 14: The Turn

**Status:** ⏳ Pending · **Goal:** The most important day in the game. Broken cart blocker, Seller stall, 3-tier approach detection, JS-01 jumpscare (eyes), purchase/refuse with doorstep fallback, full Act 1 finale cinematic with F# sequence.

## Prerequisites
- Phases 2-6 ✅
- F# audio file ideally composed (or accept placeholder silent gap)
- Existing `main.gd::trigger_js01()` already built ✅ (3-frame overlay sequence)
- Existing `the_seller.gd` has click counter + sprite swap ✅ — just needs 3-tier detection layer

## Steps

### 7.1 — Market Day 2 setup
- [ ] **7.1.1** South gate opens (already wired Phase 4.1 — verify Day 14 path)
- [ ] **7.1.2** Add 2-3 additional ambient villager sprites to Market scene (background movement)
- [ ] **7.1.3** Tool stall: enable additional upgrade items for Day 14 (sprite + price config)
- [ ] **7.1.4** Seed stall: enable new decorative variety (cosmetic — not story-critical)

### 7.2 — Broken cart blocker
- [ ] **7.2.1** Create `scenes/market/BrokenCart.tscn` + `broken_cart.gd`. Sprites: cart + 2 horses + Driver NPC (placeholder rects OK)
- [ ] **7.2.2** Place across Market's south exit. StaticBody2D collision blocks transition zone (disable exit Area2D's `monitoring`)
- [ ] **7.2.3** Driver NPC: Interactable. Dialogue `DialogueManager.start_dialogue("driver", "blocker_intro")` (already in JSON ✅)
- [ ] **7.2.4** Approach tooltip on exit attempt: `"The way out is blocked. A cart with a broken wheel."`
- [ ] **7.2.5** On `day_started(14)` and entering Market → spawn cart, disable exit

### 7.3 — Seller stall activation
- [ ] **7.3.1** Day 14: enable Seller sprite at north-edge stall (Phase 4 hid it for Day 7)
- [ ] **7.3.2** Seller has **NO idle animation** — the only character with no _sway_t. This is the only character motionless in a scene full of motion. Remove or stub `_process()` sway code in `the_seller.gd` for Day 14
- [ ] **7.3.3** Cloth seed pouch sprite on stall table

### 7.4 — Three-tier approach detection
- [ ] **7.4.1** In `the_seller.gd`, add two Area2D children: `OuterRing` (radius `5 * TILE_SIZE`), `InnerRing` (radius `3 * TILE_SIZE`). Connect `body_entered` signals to detect Elias
- [ ] **7.4.2** Outer ring entry: `AudioManager.set_layer_volume_db("guitar", -3.0)` then schedule restore in 3.3s (1 bar at 72 BPM). Reduce market_chatter ambient -3dB
- [ ] **7.4.3** Inner ring first entry: auto-trigger dialogue `the_seller.first_click` (already in JSON ✅, contains "Rare specimen." line)
- [ ] **7.4.4** Inner ring second pass without interacting: trigger second line of `first_click` array, or new state `"second_pass"`
- [ ] **7.4.5** Direct interaction (E or click): existing flow continues — full dialogue tree → purchase choice (existing logic preserves ✅)

### 7.5 — JS-01 jumpscare verification
- [ ] **7.5.1** Existing `the_seller.gd::_fire_js01()` already wired ✅. Calls `main.trigger_js01()`. Existing `main.gd::trigger_js01()` runs 3-frame overlay ✅
- [ ] **7.5.2** **Bible spec verification**: 0.3s total at correct color. Existing code uses 0.1s per frame × 3 = 0.3s ✅. Check that frame 2's Seller sprite swap uses `Constants.PALETTE_RESERVED.SELLER_EYE` (Color 0.66, 0.71, 0.63) — currently loads `EYES_OPEN_TEXTURE_PATH` SVG which may not match. **Either**: (a) author proper SVG with reserved color, or (b) generate runtime sprite using palette color
- [ ] **7.5.3** Audio: `AudioManager.play_sfx("js01_low_tone")` synced with overlay. Verify cuts to silence after sting
- [ ] **7.5.4** After JS-01: `GameState.seller_examined_twice = true` (existing ✅), dialogue resumes with `js01_post`/"Will that be all." (already in JSON ✅)

### 7.6 — Purchase / refuse mechanics
- [ ] **7.6.1** Existing `_show_purchase_choice` ✅ — verify it still works post-refactor. Uses `DialogueBox.show_choices` + `choice_made` signal
- [ ] **7.6.2** Buy + gold >= 5: existing flow ✅ (modify_gold, seed_obtained=true, save)
- [ ] **7.6.3** Buy + gold < 5: ADD fallback. Show `"Not enough gold."` line, treat as refuse outcome
- [ ] **7.6.4** Refuse: existing `walk_away` dialogue ✅. On `day_started(15)` doorstep delivery already wired in DayManager ✅ — verify seed sprite spawns on farmhouse doorstep with Bruno (if present) sitting beside facing away

### 7.7 — Cart unblock
- [ ] **7.7.1** Subscribe to `DialogueManager.dialogue_finished` for Seller dialogues. When Seller dialogue ends (any outcome), trigger cart unblock
- [ ] **7.7.2** Driver gains new dialogue state `unblock` (already in JSON ✅). On approach after unblock, can interact for one final line
- [ ] **7.7.3** Cart slide-off animation: Tween cart position off-path (1.5s). Driver tips head, despawn
- [ ] **7.7.4** Re-enable Market south exit Area2D
- [ ] **7.7.5** Wheelwright boy detail: spawn `WheelwrightBoy.tscn` (new — sprite that runs east→west across market 2s during cart-fix sequence). Single frame where his head turns toward Seller stall position. No tooltip

### 7.8 — Walk home
- [ ] **7.8.1** Existing exit flow: player walks through south exit → `main.go_to_farm()`. Should "just work" once cart unblocked
- [ ] **7.8.2** Verify Bruno at gate (if present) — existing Bruno WAITING_AT_GATE state from Phase 3.2.4 should trigger Day 14 too
- [ ] **7.8.3** Evening at farm should be normal — no immediate visual changes (Bible: "everything as they left it")

### 7.9 — Day 14 night cinematic (Act 1 finale)
- [ ] **7.9.1** Create `scenes/cutscenes/Act1Finale.tscn` + `act1_finale.gd`. Triggered when player sleeps on Day 14
- [ ] **7.9.2** Hijack normal sleep flow on Day 14: instead of standard DayTransition, instantiate Act1Finale
- [ ] **7.9.3** Cutscene sequence (player control disabled throughout):
  1. Normal Day 14 journal opens (existing flow with new Bible journal text ✅)
  2. On journal close: auto-walk Elias to window (Tween position), camera pans
  3. 3s hold on farm-through-window view (just a static visual)
  4. Auto-walk to bed, lie down, fade to black (1s ColorRect Tween)
- [ ] **7.9.4** Black screen audio timeline (use Timer nodes or `await get_tree().create_timer().timeout`):
  - t=0.0s: existing farm loop continues
  - t=2.0s: quarter-rest beat (already baked into Days-12+ piano variant ✅)
  - t=2.5s: `AudioManager.play_sfx("f_sharp")` — one-shot, dry, slightly detuned
  - t=3.5s: `AudioManager.stop_all()` (hard cut to silence)
  - t=5.5s: title card fade-in "ACT 1 — THE GOOD LIFE — COMPLETE" (Label, pixel font white on black, no animation)
  - t=8.5s: title card fade out (1s Tween)
  - t=9.5s: silence
  - t=12.5s: `AudioManager.play_sfx("f_sharp_reverb")` — softer, with reverb (THE ONLY REVERB IN ACT 1)
  - t=14.5s: fade to silence
  - t=15.0s: begin Day 15 transition (call `DayManager.advance_day()`)

### 7.10 — Day 15 morning handoff
- [ ] **7.10.1** On `day_started(15)`: AudioManager calls `play_broken_motif()` instead of regular morning theme. The broken motif track plays 2 notes of E-G-A then pauses then variation (already in audio_requests.json ✅)
- [ ] **7.10.2** Doorstep seed: if not `seed_obtained` via buy → spawn SeedPouch sprite at farmhouse doorstep (Phase 7.6.4 already wired ✅ via DayManager)
- [ ] **7.10.3** Bruno (if present) sits beside seed pouch, facing away. Override Bruno default morning position
- [ ] **7.10.4** This is the **end of Act 1 scope**. Act 2+ planting + plant whisper systems are out of scope

## Files touched (expected)
- `scenes/market/Market.tscn` (cart placement, ambient villagers, additional stalls)
- `scenes/market/BrokenCart.tscn` + `broken_cart.gd` (new)
- `scenes/market/WheelwrightBoy.tscn` + script (new)
- `scenes/npcs/the_seller.gd` (Outer/InnerRing Area2D children, sway disable Day 14)
- `scenes/npcs/TheSeller.tscn` (add Area2D children)
- `scenes/cutscenes/Act1Finale.tscn` + `act1_finale.gd` (new)
- `scenes/ui/day_transition.gd` (Day 14 hijack)
- `assets/sprites/seller_eyes_open.svg` (verify or recreate with reserved color)

## Verification (smoke tests)
- [ ] Day 14 morning: south gate opens, market loads, cart blocks exit
- [ ] Driver dialogue plays
- [ ] Walk past Seller at 5-tile range: market chatter + guitar dip
- [ ] Inner 3-tile range: auto-dialogue "Rare specimen."
- [ ] Direct interact: full Seller dialogue
- [ ] Second click: JS-01 fires (0.3s, correct color, low tone)
- [ ] Buy with 5g: pouch in inventory, gold deducted
- [ ] Refuse: walk away dialogue, Day 15 doorstep delivery works
- [ ] Buy with 0g: fallback to refuse path
- [ ] Cart unblocks after Seller dialogue ends
- [ ] Wheelwright boy plays with head turn
- [ ] Sleep Day 14 → finale cutscene plays full 15s sequence
- [ ] F# audible at 2.5s, second F# (with reverb) at 12.5s
- [ ] Title card displays correctly
- [ ] Day 15 morning: broken motif plays (or silent if file absent)
- [ ] Refused path: SeedPouch on doorstep, Bruno facing away

## Open questions
1. Seller's eyes-open sprite — recreate the SVG with `Constants.PALETTE_RESERVED.SELLER_EYE` or runtime tint a placeholder?
2. Title card font — use existing project font or commission pixel-handwriting font?
3. Hijacking the Day 14 sleep flow — replace DayTransition entirely or insert before it?
4. Camera pan to window: needs separate `WindowPanCamera` or repurpose main Camera2D with Tween?
5. F# audio missing — accept silent gap in cinematic or block on composition?
