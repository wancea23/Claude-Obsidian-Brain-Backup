# NPC Trust

## Storage
- `GameState.npc_trust: Dictionary` — keyed by NPC id string
- Range: -5 to +5 per NPC
- Persisted in save file

## Trust events (Act 1)

### Margaret
| Action | Delta | Condition |
|--------|-------|-----------|
| Help fix fence | +1 | `margaret_helped = true` |
| Ignore fence entirely | -1 | Day 10 passes with fence unrepaired |
| Sell crops at fair price | +1 | Player accepts offered rate |
| Overcharge (player perspective) | -1 | Player pays above market |

### The Seller
| Action | Delta | Note |
|--------|-------|------|
| Any interaction | +1 | He seems to like being watched |

## Act 2+ effects
- Trust score affects dialogue variant selection (high / neutral / low branches)
- Margaret trust < 0: she stops delivering bread
- The Seller trust ≥ 3: unlocks a rare seed type hint in Act 2
- Full implementation pending Act 2 design pass

## Implementation note
- Trust changes are applied via `GameState.npc_trust[npc_id] = clamp(val, -5, 5)`
- Events are fired from `farm_sidequests.gd` and `DayManager._fire_day_events()`
