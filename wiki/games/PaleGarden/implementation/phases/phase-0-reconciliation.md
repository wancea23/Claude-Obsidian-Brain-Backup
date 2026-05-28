# Phase 0 — Reconciliation & Asset Prep

**Status:** ✅ Done · **Goal:** Audit existing code against Bible, prep cross-cutting assets (palette, JSON content, audio bus, GameState flags). No gameplay code changes.

## Completed steps

- ✅ **0.1** Audit existing code → `Games/PaleGarden/audit.md` (Bible↔code coverage map, ~55%)
- ✅ **0.2** Restructure palette in `globals/Constants.gd` — `PALETTE_ACT1` (22 named warm colors) + `PALETTE_RESERVED` (Act 2+ tones inc. `SELLER_EYE`). Fixed cold-blue legacy aliases (night, sky, Margaret dress, roof)
- ✅ **0.3** Migrate `content/events.json` — Margaret moved Day 10→7, `scarecrow_rot` deleted, added `crow_arrival_first`/`second`, `bread_delivery_start`, `broken_cart_blocker`, `scarecrow_items_unlock`, `porch_evening_unlock`
- ✅ **0.3** Rewrite `content/journal_entries.json` to Bible voice with `_bruno_absent` variants (Days 4-13), `6_journal_full/partial`, `11_no_scarecrow`, `%BRUNO_NAME%` substitution tokens
- ✅ **0.3** Extend `content/npc_dialogue.json` — Margaret `greeting_day7`, `fence_intro_day7`, `fence_repair_chat`, `tea_scene` (with the "we" slip line), new `driver` NPC, narrator crow tooltips
- ✅ **0.3** Create `content/old_journal.json` — 5 entries with `handwriting_style: 0-4` (Bible §Part 8)
- ✅ **0.3** Extend `globals/DialogueManager.gd` — variant selection (bruno_absent / journal_full/partial / no_scarecrow), `%BRUNO_NAME%` substitution, `get_old_journal_entries()` API
- ✅ **0.4** Create `default_bus_layout.tres` — Master → Music (Piano/Guitar/Percussion subbuses, layers default to -80dB) → Ambient (Wind/Birds/Misc) → SFX
- ✅ **0.4** Extend `audio_requests.json` with 30 Act 1 Bible-spec entries (themes, layers, ambient, SFX)
- ✅ **0.5** Extend `globals/GameState.gd` — added `bruno_present`, `old_journal_pages_read`, `tutorial_complete`, `has_scarecrow_post/coat/straw`. Converted `conscience` float→int. Added `set_flag`/`get_flag` API. Full save/load round-trip
- ✅ **DayManager fix** — bread cadence daily from Day 8+ (was every-7-days from Day 10). Day 15 doorstep delivery preserved
- ✅ **CLAUDE.md fix** — `Games/CLAUDE.md` Godot 4.3 → 4.6

## Resolved decisions
1. Hunger scale: keep 0-10
2. Conscience: convert to `int 0-100`
3. EventBus autoload: skip (existing direct signals work)
4. Cardinal NPC: scope "rebuild content" — delete in Phase 2 cleanup
5. Godot version: 4.6 (updated CLAUDE.md)
6. Scope: keep framework, rebuild content
7. Audio: user creates music; placeholder slots in `audio_requests.json`

## Verification
- `Godot.exe --headless --path . --quit` → clean load, no parse errors
- Save/load round-trip not yet runtime-tested (deferred to Phase 8 smoke tests)

## Open follow-ups
- Cardinal cleanup → moved to Phase 2 prep
- Hunger UI exposure (was visible in existing scene) → review when touching HUD in Phase 2
