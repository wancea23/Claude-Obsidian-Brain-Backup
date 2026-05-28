# Act 1 Implementation Phases

User-driven step-by-step build. I do nothing until you say "do step X.Y".

> **2026-05-28**: Main scene switched to `scenes/world/yard.tscn` (Yard redesign).
> Yard foundation work (Elias spawn/walk/collide, garden zone, crop sprite renderer,
> 4×4 grid) is logged at the top of [[phase-2-days-1-3#Yard redesign — completed 2026-05-28]].
> Phase 1 ✅ marks still apply to the legacy `Farm.tscn` systems, but the Farm→Farmhouse
> transition listed there is now obsolete (see Phase 1 "Post-redesign state").

| # | Phase | Status | Doc |
|---|-------|--------|-----|
| 0 | Reconciliation & Asset Prep | ✅ Done | [[phase-0-reconciliation]] |
| 1 | Foundation Systems Upgrade | ✅ Done (Farm.tscn era) | [[phase-1-foundation]] |
| 2 | Days 1-3 Foundation Experience | 🟡 In progress (Yard foundation done, Day 1 tutorial pending) | [[phase-2-days-1-3]] |
| 3 | Days 4-6 Bruno & Old Journal | ⏳ Pending | [[phase-3-days-4-6]] |
| 4 | Day 7 Market & Margaret | ⏳ Pending | [[phase-4-day-7]] |
| 5 | Days 8-11 Disruption | ⏳ Pending | [[phase-5-days-8-11]] |
| 6 | Days 12-13 Peak Polish | ⏳ Pending | [[phase-6-days-12-13]] |
| 7 | Day 14 — The Turn | ⏳ Pending | [[phase-7-day-14]] |
| 8 | Full Verification & Polish | ⏳ Pending | [[phase-8-verification]] |

## Reference
- Macro plan: [[../act1-build-plan]]
- Codebase audit: `Games/PaleGarden/audit.md`
- Story bible: `Games/PaleGarden/story/act1/act1.md` + `act1 addition.md`

## How to drive
- "do step 2.1" → I execute exactly that step
- "skip step 3.4" → I mark it skipped with note
- "redo step 1.3" → I revisit and adjust
- "all of phase 2" → I do every pending step in order, checking in only on blockers
- "block on me for step X" → before doing X, I AskUserQuestion for the decision
