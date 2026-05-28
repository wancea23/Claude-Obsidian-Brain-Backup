# Act 1 Storyline Graph — The Pale Garden

## Start
→ [[events/tutorial-start]] (Day 1)
→ [[events/crops-growing]] (Days 2-3)
→ [[events/bruno-arrive]] (Day 4)
  - Keep Bruno → `bruno_named = true` → [[events/bruno-follows]]
  - Shoo Bruno → `bruno_named = false` → Bruno gone by Day 7

→ [[events/back-field-expand]] (Day 6)
  - Dig back field → journal_surface (conditional: `back_field_tilled`)
  - Find old journal → `journal_read` option

→ [[events/market-day-1]] (Day 7)
  - The Seller visible but unreachable
  - Standard market trades

→ [[events/scarecrow-rot]] (Day 9)
  - Complete repair → scarecrow faces garden → foreshadows JS-02

→ [[events/margaret-fence-fall]] (Day 10-11)
  - Repair → `margaret_helped = true` → bread deliveries + alliance path
  - Ignore → `margaret_helped = false` → trust -1

→ [[events/market-day-2]] (Day 14)
  - [[events/seller-encounter]] (cannot skip)
    - Buy seed → `seed_obtained = true` → Act 2 begins Day 15
    - Walk away → seed appears on doorstep Day 15 → `seed_obtained = true`

## Act 1 Endings (none — Act 1 always leads to Act 2)
All paths converge at Day 15. The seed is always planted. The game is patient.

## Locked by Act 1 choices (affects Act 2+)
- `bruno_named` → determines Act 3 path A availability
- `margaret_helped` → determines Act 4 alliance availability
- `journal_read` → unlocks extra dialogue in Act 2 whisper scenes
- `conscience` score starts here (fence repair +1, each fair market trade +1)
