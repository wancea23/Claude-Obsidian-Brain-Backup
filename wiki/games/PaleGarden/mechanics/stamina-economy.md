# Stamina Economy

## Values
- Max: `Constants.STAMINA_MAX` = 5 per day
- Reduced to 3 if player is starving (`GameState.hunger <= Constants.HUNGER_WASTING_THRESHOLD`)
- Stored in `GameState.stamina: int`

## Costs per action (Constants.gd)
| Action | Cost |
|--------|------|
| TILL | 1 |
| WATER | 1 |
| PLANT | 1 |
| REAP (pick) | 1 |

## Display
- 5 `ColorRect` dots in HUD (`scenes/ui/HUD.tscn`)
- Filled = `DOT_FILLED` (amber), empty = `DOT_EMPTY` (dark)
- Also shown inside GardenOverlay for context while gardening

## Reset
- `DayManager.advance_day()` sets `GameState.stamina = Constants.STAMINA_MAX`
- Then immediately clamps to 3 if hunger wasting applies (see [[mechanics/hunger-system]])
- Emits `GameState.stamina_changed`

## UI lockout
- At stamina 0: all action buttons in GardenOverlay are disabled
- `GardenOverlay.lock_tools([])` called when stamina reaches 0
