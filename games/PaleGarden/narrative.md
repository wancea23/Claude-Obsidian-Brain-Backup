---
project: The Pale Garden
type: narrative summary
last_updated: 2026-04-30
---

# Narrative — Story Spine

Authoritative source: `Code/Games/PaleGarden/story-sketch.md` (4,500+ word GDD). This file summarises the spine for cross-referencing in code.

## 5-act structure (52 days, ~4.5 hours)

| Act | Days | Tone | Implementation status |
|---|---|---|---|
| 1. The Good Life | 1–14 | Cozy farm sim, zero horror | **In progress** — map, walking, garden loop, stamina, time-of-day all working |
| 2. The Awakening | 15–25 | Curious → wrong | Not started — needs blood plant + whisper system |
| 3. The Feeding | 26–35 | Dread, first gore | Not started |
| 4. The Hunger Season | 36–45 | Full horror | Not started |
| 5. The Reckoning | 46–52 | Path-locked endings | Not started |

## Act 1 beats (relevant for current build)

- **Day 1**: Tutorial. Narrator: "Another quiet morning." Player learns to till.
- **Day 2**: Back field unlock event (`back_field_expand`).
- **Day 3**: Margaret's fence falls (`margaret_fence_fall`) — fence repair minigame.
- **Day 4**: Bruno arrives (`bruno_arrive`) — naming popup.
- **Day 6**: Old journal surfaces (`journal_surface`) — only if back field tilled. Reads "Do not plant what the stranger sells."
- **Day 7**: Market Day 1 (`market_day_1`) — bartering minigame, Margaret stall.
- **Day 9**: Scarecrow rot (`scarecrow_rot`) — rebuild minigame.
- **Day 14**: Market Day 2 + Seller encounter (`market_day_2`, `seller_encounter`). JS-01 jumpscare wired.
- **Day 15**: Doorstep seed delivery (if walked away from Seller).

## Characters

| ID | Role | Implementation |
|---|---|---|
| Elias | Player (silent farmer) | Bone-coloured walking placeholder with eyes |
| Margaret | Neighbour, fence sidequest, market stall | Blue-dress placeholder, event-driven spawn only |
| Bruno | Optional dog companion | Tan dog placeholder, ambient spawn from Day 4 |
| The Seller | Day 14 market stranger, JS-01 trigger | Black-coat hat placeholder, event-driven |
| Father Dorin | Day 33 visit (Act 3) | Not implemented |
| The Plant | Day 15+ corruption focus (Act 2+) | Not implemented |

## Tone rules (from STYLE.md)
- Plants are aware. Soil remembers.
- Short sentences. Cryptic. Never explanatory.
- No exclamation points. No modern slang. No humor.
- NPCs sound confused.
- Whispers are first-person plural ("we taste the rain").
- Dialogue is second-person to player ("you brought us something").

## Visual tone shift between Acts
- Act 1 = warm green pastoral palette (`COLOR_ACT1_*`)
- Act 2+ = STYLE.md gothic dark palette (`COLOR_BG`, `COLOR_BLOOD`, etc.) — kicks in when blood plant is planted
- This shift is **intentional and load-bearing** — see [[decisions.md]]
