# Phase 8 — Full Verification & Polish

**Status:** ⏳ Pending · **Goal:** Confirm Act 1 holds together end-to-end. Three smoke-test playthroughs, palette audit, edge cases, Act 2-5 hook verification.

## Prerequisites
- Phases 2-7 ✅
- All Bible audio files in place (or accept silent placeholders documented)

## Steps

### 8.1 — Smoke test scripts
- [ ] **8.1.1** Create `tests/run_act1_smoke.gd` — automated playthrough using fast-forward time. Uses `DayManager.advance_day()` + scripted choices
- [ ] **8.1.2** Three runs:
  - **Max positive**: Bruno kept+named, fence helped, scarecrow built, journal all 5 read, buy seed
  - **Max minimal**: Bruno shooed, no fence, no scarecrow, no journal, refuse seed
  - **Middle**: Bruno kept unnamed, fence helped, no scarecrow, journal partial, buy seed
- [ ] **8.1.3** Each run completes without errors; final GameState flag dump matches expected matrix (assertion table)
- [ ] **8.1.4** Run via `Godot.exe --headless --script tests/run_act1_smoke.gd`

### 8.2 — Visual QA (palette audit)
- [ ] **8.2.1** Screenshot every time-of-day phase on every day via Godot MCP. 14 days × 6 phases = 84 screenshots saved to `tests/screenshots/`
- [ ] **8.2.2** Manual review: no cold tones anywhere except JS-01 eye flash. Spot-check Day 14 night (used to be blue — should now be warm-dark)
- [ ] **8.2.3** Create `tools/palette_audit.gd` — loops sprites in `assets/sprites/`, samples colors, fails build if any color not in `PALETTE_ACT1` or `PALETTE_RESERVED.SELLER_EYE`

### 8.3 — Audio QA
- [ ] **8.3.1** Listen to full Day 1, Day 7, Day 14 playthroughs
- [ ] **8.3.2** Verify layer additions: Day 4 guitar in, Day 8 percussion in, Day 12 quarter-rest variant
- [ ] **8.3.3** Verify F# sequence timing (Phase 7.9.4) — both F# notes at correct moments
- [ ] **8.3.4** Verify NO reverb anywhere except final F# (the only intentional reverb in Act 1)
- [ ] **8.3.5** Verify NO bass below 200Hz — apply Master bus EQ if not already

### 8.4 — Edge case sweep
- [ ] **8.4.1** Skip tutorial — does game still play? (Phase 2.1 should set `tutorial_complete` only on completion; abandon path?)
- [ ] **8.4.2** 0 gold on Day 14 — fallback to refuse outcome works
- [ ] **8.4.3** Never till back-left corner — game completable, Old Journal stays buried
- [ ] **8.4.4** Shoo Bruno Day 4 — full Bruno-absent playthrough completes
- [ ] **8.4.5** Refuse Margaret fence — no bread, game still playable, Day 14 still reachable

### 8.5 — Save/load test
- [ ] **8.5.1** Save mid-Day-7 fence minigame, quit, reload → resumes at start of Day 7 (acceptable per autosave-on-day_started design)
- [ ] **8.5.2** All flags survive round-trip — extend test script
- [ ] **8.5.3** Document in player-facing settings (or future MainMenu copy): "Game saves at the start of each day"

### 8.6 — Act 2-5 hook audit
Verify required hooks present in `decisions.md`:
- [ ] **8.6.1** `bruno_name` preserved verbatim for Act 3 plant dialogue (test: name Bruno "Biscuit" → save → reload → confirm string)
- [ ] **8.6.2** `journal_read` controls Act 2 whisper unlock placeholders
- [ ] **8.6.3** `margaret_helped` controls Act 4 alliance availability
- [ ] **8.6.4** `scarecrow_rebuilt` controls Act 2 Day 22 scarecrow turn (placeholder log message OK in Act 1)
- [ ] **8.6.5** `crow_system.gd` supports silence-from-Day-15+ (absence = horror cue)
- [ ] **8.6.6** Bruno collar audio silenceable when Bruno gone (Act 3 sacrifice)
- [ ] **8.6.7** Quarter-note rest in music loop has hook for filling with whisper/F# in Act 2
- [ ] **8.6.8** Journal handwriting system supports styles 0-4 (Old Journal already does ✅ — verify Elias journal Day 14 onward can adopt)
- [ ] **8.6.9** Farmhouse props have hooks for Act 3-5 transformations (photograph, chair, cup positions documented)

### 8.7 — Vault updates
- [ ] **8.7.1** Update `graphify-out/wiki/games/PaleGarden/overview.md` — mark Act 1 complete, update date
- [ ] **8.7.2** Append `graphify-out/wiki/games/PaleGarden/chat-history.md` with implementation session summary
- [ ] **8.7.3** Update `decisions.md` with all Act 1-built hooks for Acts 2-5
- [ ] **8.7.4** Mark all phase docs ✅ in `implementation/phases/index.md`

## Files touched (expected)
- `tests/run_act1_smoke.gd` (new)
- `tools/palette_audit.gd` (new)
- `tests/screenshots/` (output folder)
- `graphify-out/wiki/games/PaleGarden/overview.md`
- `graphify-out/wiki/games/PaleGarden/chat-history.md`
- `graphify-out/wiki/games/PaleGarden/decisions.md`
- `graphify-out/wiki/games/PaleGarden/implementation/phases/index.md`

## Verification (meta — this phase verifies itself)
- [ ] All 3 smoke tests pass
- [ ] No cold tones in any screenshot except JS-01
- [ ] All audio cues fire at correct days
- [ ] All edge cases graceful
- [ ] Save/load works
- [ ] All Act 2-5 hooks documented

## Open questions
1. Smoke test framework: hand-rolled, or use GUT (Godot Unit Test) addon?
2. Screenshot audit: take all 84 manually with MCP, or batch via script that advances day+phase and captures?
3. Player-facing save documentation: in MainMenu help screen, or settings panel, or both?
