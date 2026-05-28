# Bruno AI

## Appearance
- Bruno arrives Day 4 via `bruno_arrive` event (events.json)
- Player is prompted to name him or shoo him away

## States
| State | Condition | Behavior |
|-------|-----------|----------|
| IDLE | `!GameState.bruno_named` | Sits, sways, clickable |
| FOLLOWING | `GameState.bruno_named` and dist > FOLLOW_DIST | Moves toward player at 60px/s |
| AVOIDING_NORTH | Would cross `NORTH_LIMIT_Y` | Clamps Y, stops at boundary |

## Follow constants (bruno.gd)
| Constant | Value | Meaning |
|----------|-------|---------|
| `FOLLOW_DIST` | 64.0 | ~2 tiles in world units |
| `NORTH_LIMIT_Y` | 200.0 | World Y of back field boundary |
| `MOVE_SPEED` | 60.0 | px/s while following |

## North field avoidance
- Bruno **will not enter the back field** (world Y < 200)
- This is a **subtle early warning** — the player notices before the horror is explicit
- If following would take Bruno past the limit, his Y is clamped to `NORTH_LIMIT_Y`

## Daily bark
- Once per day (reset in `_on_day_started`), Bruno faces north and barks
- Random delay 3–8 s after day start (feels natural, not scripted)
- Plays `AudioManager.play_sfx("dog_bark")`
- Only triggers if `GameState.bruno_named` is true

## Shoo path
- Player clicks Bruno before naming → NamingPopup → rejects name
- `_on_name_rejected()`: plays "shooed" dialogue, tweens Bruno off screen (x = -60), then `queue_free()`
- `GameState.bruno_named` stays false; Bruno does not reappear in Act 1

## Player ref wiring
- `@export var player_ref : NodePath` — set in Farm.tscn inspector to point at Elias node
- Falls back gracefully if empty (Bruno sits idle)
