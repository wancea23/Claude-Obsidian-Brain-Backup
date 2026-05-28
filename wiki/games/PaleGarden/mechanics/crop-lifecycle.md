# Crop Lifecycle

## Phases (Constants.gd)
| Value | Constant | Display |
|-------|----------|---------|
| 0 | CROP_SEED | tiny dot |
| 1 | CROP_SPROUT | small green shoot |
| 2 | CROP_BLOOM | mid-height plant |
| 3 | CROP_HARVEST | ripe fruit visible |
| 4 | CROP_WILT | drooped, grey tint |

## Progression rules
- Advances one phase per day **if watered** that day
- If not watered during SEED phase: `has_weed = true` (weedy growth, penalises yield)
- HARVEST → WILT automatically if player does not reap on the harvest day

## Crop types (Act 1)
| Type | Sell price | Notes |
|------|------------|-------|
| Turnip | 3g | fastest, 3-day grow |
| Tomato | 8g | mid tier |
| Pumpkin | 15g | slow, back-field only at start |

## Sprites
- Each phase uses `assets/sprites/crop_<type>_<phase>.svg` (will become .png for Act 2)
- Drawn procedurally in `crop.gd` `_draw()` using Constants palette until sprites land

## Harvest
- Player selects REAP tool → clicks HARVEST-phase tile
- Calls `GameState.add_crop(type)` + `GameState.modify_gold(price)`
- Emits `inventory_changed`

## Wilt
- Crop node phase set to CROP_WILT, `is_dead = true`
- Next day-advance: Garden removes dead crop from tile, resets to `tilled`
