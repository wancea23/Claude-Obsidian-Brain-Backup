# Phase 1 — Foundation Systems Upgrade

**Status:** ✅ Done (code-only; runtime-untested) · **Goal:** Cross-cutting systems every later phase depends on (TimeManager autoload, time-of-day shader fix, layered audio, Interactable component, Old Journal UI, Farmhouse scene shell).

## Completed steps

- ✅ **1.1** `globals/TimeManager.gd` autoload — `Phase` enum (DAWN/MORNING/AFTERNOON/GOLDEN_HOUR/DUSK/NIGHT), `phase_changed` + `phase_progress` signals, helpers `is_night()`, `pause()`, `resume()`, string↔phase conversion. Drives off existing stamina-action economy. Mirrors string to legacy `GameState.time_of_day`
- ✅ **1.1** Registered `TimeManager` in `project.godot` autoloads
- ✅ **1.2** Refactor `scenes/world/time_of_day.gd` — subscribes to `TimeManager.phase_changed`, pulls colors from `Constants.TIME_OF_DAY_COLORS`. **Cold-blue night bug fixed**
- ✅ **1.3** Full rewrite `globals/AudioManager.gd` — layered music API (`play_music_layer`/`stop`/`set_volume_db` for piano/guitar/percussion), theme one-shots (`play_morning_theme`, `play_market_theme`, `play_broken_motif`), ambient bus API (`play_ambient`/`stop_ambient`), day-driven auto-layering on `day_started`, bus-aware player creation, SFX preload extended with all Bible entries. Placeholder-safe (silent if file absent). Legacy `play_music()` + crossfade preserved
- ✅ **1.4** `scripts/components/interactable.gd` — reusable `class_name Interactable extends Area2D`. `text_variants` Dictionary keyed by condition strings (`default`, `day>=N`, `day<N`, `day==N`, `flag:name`, `noflag:name`). Empty string = inert. Emits `interacted` + `interaction_text`
- ✅ **1.5** `scenes/ui/old_journal.gd` + `OldJournal.tscn` — page nav (prev/next/close), BBCode color tint per `handwriting_style` (0=neat → 4=shaky), tracks `GameState.old_journal_pages_read` max, sets `journal_read=true` when all 5 viewed
- ✅ **1.6** `scenes/farmhouse/farmhouse.gd` + `Farmhouse.tscn` — interior shell with all Bible props (Photograph "Not today.", DustyCup, SecondChair, Bookshelf, CoatNail w/ scarecrow-part hooks, NorthWindow w/ Day 8+ Margaret light, Bed, JournalDesk, Door). **ColorRect placeholders for visuals — not real art**
- ✅ `scenes/main.gd` — added `go_to_farmhouse()` matching `go_to_farm()`/`go_to_market()` pattern

## Verification
- `Godot.exe --headless --path . --quit` → clean load
- **Runtime behavior NOT verified** — bus routing, layered playback, day-scheduling logic, Interactable variant evaluator, farmhouse interactions all unverified at runtime. Will surface during Phase 2 first playthrough or Phase 8 smoke tests

## Known debts (rolled into Phase 2 prep)
- ~~Farm → Farmhouse transition wiring missing (Farm.tscn has `FarmhouseCollider` but no `Main.go_to_farmhouse()` call)~~ — **obsolete 2026-05-28**: main scene is now `yard.tscn`, not `Farm.tscn`. The new transition lives in `yard_zones.gd` (House door zone, not yet built — see [[phase-2-days-1-3#Yard redesign — completed 2026-05-28]]).
- Bookshelf 5 lines hardcoded in `farmhouse.gd` as `BOOKSHELF_LINES` array — violates "all strings from `content/*.json`" rule. Move to `content/npc_dialogue.json` under `bookshelf` block
- Farmhouse visuals are placeholder rectangles — real tilemap + props sprites need composing
- Audio files don't exist yet — system wired but everything plays silent until composition lands

## Post-redesign state (2026-05-28)

The new yard.tscn doesn't use `time_of_day.gd` or the `TimeManager` autoload yet — the `Background/SkyRect` ColorRect is a static dark-green. Phase 2's Yard work (above) didn't touch the day/time wiring. The TimeManager autoload still exists and works; it's just not connected to anything visible on the Yard. See Phase 2 todo list.
