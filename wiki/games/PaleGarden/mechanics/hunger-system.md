# Hunger System

## Values
- Start: `Constants.HUNGER_START` = 5
- Max: `Constants.HUNGER_MAX` = 10
- Min: 0
- Stored in `GameState.hunger: int`

## Drain
- Decreases by 1 each day via `DayManager.advance_day()` → `GameState.modify_hunger(-1)`

## Display
- `HUD._hunger_label` shown from Day 5 onward
- Color coding (implemented in `hud.gd`):
  - hunger > 4 → `Color.WHITE`
  - hunger 3–4 → `Constants.COLOR_BONE` (pale caution)
  - hunger ≤ 2 → `Constants.COLOR_BLOOD` (red warning)

## Wasting mechanic (DESIGN DECISION)
- Threshold: `Constants.HUNGER_WASTING_THRESHOLD` = 1
- When `GameState.hunger <= 1`: stamina cap is reduced to 3 for that day
- Applied in `DayManager.advance_day()` after stamina restore
- This means the player physically cannot do more than 3 garden actions while starving
- Margaret's bread delivery restores +2 hunger

## Food sources (Act 1)
- **Margaret's bread**: delivered every 7 days after fence repair (days 10, 17, ...)
  - Triggered via `margaret_bread_delivery` event in DayManager
  - Restores +2 hunger

## Act 2 connection
- TODO: hunger tied to feeding the plant — the plant asks; player can sacrifice food
- High hunger → more dialogue options; low hunger → player is more "desperate"
